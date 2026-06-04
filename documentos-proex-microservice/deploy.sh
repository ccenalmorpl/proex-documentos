#!/bin/bash
# deploy.sh - Script automatizado de deployment para documentos-proex-microservice
#
# Este script despliega la función Lambda usando API Gateway HTTP API como método
# de exposición por defecto (en lugar de Lambda Function URL) para tener:
# - Mayor control sobre rate limiting y throttling
# - Mejor monitoreo y métricas
# - Posibilidad de añadir custom domains
# - Compatibilidad con todas las regiones AWS
#
# Variables de entorno requeridas en .env:
#   PROEX_ACCESS_TOKEN           - HubSpot private app access token
#   CORS_ORIGINS                 - Orígenes CORS permitidos (CSV)
#   SANITARIO_EMPRESA_DIRECCION  - Texto fijo empresa+dirección para certificado sanitario
#   SANITARIO_ESTABLECIMIENTO    - Establecimiento fijo del certificado sanitario
#   SANITARIO_JEFE_SALUD         - Jefe de salud fijo del certificado sanitario
#   SANITARIO_FIRMADO_EN         - Lugar de firma fijo del certificado sanitario
#   FILES_FOLDER                 - Carpeta destino en HubSpot File Manager
#   AWS_REGION, AWS_ACCOUNT_ID, ECR_REPO_NAME, FUNCTION_NAME

set -e  # Exit on error

# Cargar variables
source .env

# AWS Profile (cambiar si usas otro perfil)
AWS_PROFILE=${AWS_PROFILE:-biatic}

echo "🚀 Iniciando deployment de ${FUNCTION_NAME}..."
echo "📌 Using AWS Profile: ${AWS_PROFILE}"

# Check if ECR repository exists, create if not
echo "🔍 Checking ECR repository..."
if ! aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} --profile ${AWS_PROFILE} &>/dev/null; then
  echo "📦 Creating ECR repository ${ECR_REPO_NAME}..."
  aws ecr create-repository \
    --repository-name ${ECR_REPO_NAME} \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} \
    --image-scanning-configuration scanOnPush=true
  echo "✅ ECR repository created successfully"
else
  echo "✅ ECR repository already exists"
fi

# Set ECR repository policy to allow Lambda access
echo "🔐 Setting ECR repository policy..."
aws ecr set-repository-policy \
  --repository-name ${ECR_REPO_NAME} \
  --region ${AWS_REGION} \
  --profile ${AWS_PROFILE} \
  --policy-text "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Sid\": \"LambdaECRImageRetrievalPolicy\",
        \"Effect\": \"Allow\",
        \"Principal\": {
          \"Service\": \"lambda.amazonaws.com\"
        },
        \"Action\": [
          \"ecr:BatchGetImage\",
          \"ecr:GetDownloadUrlForLayer\"
        ]
      }
    ]
  }" || echo "⚠️  Warning: Could not set repository policy (may already exist)"

# Build
echo "📦 Building Docker image (with --no-cache to ensure fresh build)..."
docker build \
  --platform linux/amd64 \
  --provenance=false \
  --output type=docker \
  --no-cache \
  -t ${ECR_REPO_NAME}:latest .

# Tag
echo "🏷️  Tagging image..."
docker tag ${ECR_REPO_NAME}:latest \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest

# Login ECR
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} --profile ${AWS_PROFILE} | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Push
echo "⬆️  Pushing to ECR..."
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest

# Check if Lambda function exists
echo "🔍 Checking Lambda function..."
if ! aws lambda get-function --function-name ${FUNCTION_NAME} --region ${AWS_REGION} --profile ${AWS_PROFILE} &>/dev/null; then
  echo "📦 Creating Lambda function ${FUNCTION_NAME}..."

  # Create Lambda execution role if it doesn't exist
  ROLE_NAME="${FUNCTION_NAME}-role"
  ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --profile ${AWS_PROFILE} --query 'Role.Arn' --output text 2>/dev/null || echo "")

  if [ -z "$ROLE_ARN" ]; then
    echo "📝 Creating IAM role ${ROLE_NAME}..."
    aws iam create-role \
      --role-name ${ROLE_NAME} \
      --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
          "Effect": "Allow",
          "Principal": {"Service": "lambda.amazonaws.com"},
          "Action": "sts:AssumeRole"
        }]
      }' \
      --region ${AWS_REGION} \
      --profile ${AWS_PROFILE}

    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
      --role-name ${ROLE_NAME} \
      --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
      --profile ${AWS_PROFILE}

    # Create and attach ECR access policy
    echo "📝 Creating ECR access policy..."
    ECR_POLICY_NAME="${FUNCTION_NAME}-ecr-policy"
    aws iam create-policy \
      --policy-name ${ECR_POLICY_NAME} \
      --profile ${AWS_PROFILE} \
      --policy-document "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
          {
            \"Effect\": \"Allow\",
            \"Action\": [
              \"ecr:GetAuthorizationToken\",
              \"ecr:BatchCheckLayerAvailability\",
              \"ecr:GetDownloadUrlForLayer\",
              \"ecr:BatchGetImage\"
            ],
            \"Resource\": \"*\"
          }
        ]
      }" 2>/dev/null || echo "⚠️  Policy may already exist"

    # Attach ECR policy
    aws iam attach-role-policy \
      --role-name ${ROLE_NAME} \
      --policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${ECR_POLICY_NAME} \
      --profile ${AWS_PROFILE} 2>/dev/null || \
      echo "⚠️  Could not attach ECR policy (may already be attached)"

    # Wait for role to be ready
    echo "⏳ Waiting for IAM role to be ready..."
    sleep 15

    ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --profile ${AWS_PROFILE} --query 'Role.Arn' --output text)
  fi

  # Create Lambda function
  # Nota: memory-size en 512MB — puede subirse a 1024MB si la generación de PDFs
  # necesita más recursos (reportlab + Pillow pueden ser intensivos en memoria).
  aws lambda create-function \
    --function-name ${FUNCTION_NAME} \
    --package-type Image \
    --code ImageUri=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest \
    --role ${ROLE_ARN} \
    --timeout 30 \
    --memory-size 512 \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} \
    --environment "Variables={
      PROEX_ACCESS_TOKEN=${PROEX_ACCESS_TOKEN},
      CORS_ORIGINS=\"${CORS_ORIGINS}\",
      SANITARIO_EMPRESA_DIRECCION=\"${SANITARIO_EMPRESA_DIRECCION}\",
      SANITARIO_ESTABLECIMIENTO=\"${SANITARIO_ESTABLECIMIENTO}\",
      SANITARIO_JEFE_SALUD=\"${SANITARIO_JEFE_SALUD}\",
      SANITARIO_FIRMADO_EN=\"${SANITARIO_FIRMADO_EN}\",
      FILES_FOLDER=${FILES_FOLDER}
    }"

  echo "✅ Lambda function created successfully"

  # Create API Gateway HTTP API (default method)
  echo "🔗 Creating API Gateway HTTP API..."
  API_ID=$(aws apigatewayv2 create-api \
    --name ${FUNCTION_NAME}-api \
    --protocol-type HTTP \
    --target arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:${FUNCTION_NAME} \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} \
    --cors-configuration AllowOrigins="*",AllowMethods="*",AllowHeaders="*" \
    --query 'ApiId' \
    --output text)

  echo "✅ API Gateway created with ID: ${API_ID}"
else
  echo "✅ Lambda function already exists, updating..."

  # Update Lambda code
  aws lambda update-function-code \
    --function-name ${FUNCTION_NAME} \
    --image-uri ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE}

  # Wait for code update to complete before updating config
  echo "⏳ Waiting for code update to complete..."
  aws lambda wait function-updated \
    --function-name ${FUNCTION_NAME} \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE}

  # Update environment variables
  echo "🔧 Updating environment variables..."
  aws lambda update-function-configuration \
    --function-name ${FUNCTION_NAME} \
    --environment "Variables={
      PROEX_ACCESS_TOKEN=${PROEX_ACCESS_TOKEN},
      CORS_ORIGINS=\"${CORS_ORIGINS}\",
      SANITARIO_EMPRESA_DIRECCION=\"${SANITARIO_EMPRESA_DIRECCION}\",
      SANITARIO_ESTABLECIMIENTO=\"${SANITARIO_ESTABLECIMIENTO}\",
      SANITARIO_JEFE_SALUD=\"${SANITARIO_JEFE_SALUD}\",
      SANITARIO_FIRMADO_EN=\"${SANITARIO_FIRMADO_EN}\",
      FILES_FOLDER=${FILES_FOLDER}
    }" \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE}
fi

# Wait for update
echo "⏳ Waiting for update to complete..."
aws lambda wait function-updated \
  --function-name ${FUNCTION_NAME} \
  --region ${AWS_REGION} \
  --profile ${AWS_PROFILE}

# Get API Gateway ID
API_ID=$(aws apigatewayv2 get-apis \
  --region ${AWS_REGION} \
  --profile ${AWS_PROFILE} \
  --query "Items[?Name=='${FUNCTION_NAME}-api'].ApiId" \
  --output text 2>/dev/null)

if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
  # Upsert Lambda invoke permission (siempre, en create y update)
  echo "🔐 Updating API Gateway invoke permission..."
  aws lambda remove-permission \
    --function-name ${FUNCTION_NAME} \
    --statement-id apigateway-invoke \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} 2>/dev/null || true
  aws lambda add-permission \
    --function-name ${FUNCTION_NAME} \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${AWS_REGION}:${AWS_ACCOUNT_ID}:${API_ID}/*" \
    --region ${AWS_REGION} \
    --profile ${AWS_PROFILE} > /dev/null
  echo "✅ Permission OK: API Gateway (${API_ID}) → Lambda (${FUNCTION_NAME})"
  LAMBDA_URL="https://${API_ID}.execute-api.${AWS_REGION}.amazonaws.com"
else
  echo "⚠️  API Gateway '${FUNCTION_NAME}-api' no encontrado. Revisa la consola de AWS."
  LAMBDA_URL="(no disponible)"
fi

echo "✅ Deployment successful!"
echo "📍 URL: ${LAMBDA_URL}"
echo "📊 Logs: aws logs tail /aws/lambda/${FUNCTION_NAME} --follow --profile ${AWS_PROFILE}"
