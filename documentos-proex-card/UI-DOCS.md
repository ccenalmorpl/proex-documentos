# HubSpot UI Extensions - Component Documentation

This document contains reference documentation for HubSpot UI Extension components used in the Documentos PROEX project.

## Table of Contents
- [Form](#form)
- [Input](#input)
- [NumberInput](#numberinput)
- [Select](#select)
- [DateInput](#dateinput)
- [SearchInput](#searchinput)
- [TextArea](#textarea)
- [ToggleGroup](#togglegroup)
- [Button](#button)
- [ButtonRow](#buttonrow)
- [Table](#table)
- [Statistics](#statistics)
- [StepIndicator](#stepindicator)

---

## Form

The Form component renders a form that can contain other subcomponents, such as Input, Select, and Button. Use this component to enable users to submit data to HubSpot or an external system.

### Example
```jsx
import { Form, Input, Button } from '@hubspot/ui-extensions';

const Extension = () => {
  return (
    <Form
      onSubmit={() => {
        console.log('Form submitted!');
      }}
    >
      <Input
        label="First Name"
        name="first-name"
        tooltip="Please enter your first name"
        description="Please enter your first name"
        placeholder="First name"
      />
      <Input
        label="Last Name"
        name="last-name"
        tooltip="Please enter your last name"
        description="Please enter your last name"
        placeholder="Last name"
      />
      <Button
        onClick={() => {
          console.log('Submit button clicked');
        }}
        variant="primary"
        type="submit"
      >
        Submit
      </Button>
    </Form>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| onSubmit | Function | The function that is called when the form is submitted. It will receive a RemoteEvent as an argument and its return value will be ignored. |
| autoComplete | 'on' (default) \| 'off' | Set this field to 'off' to prevent autocompletion software (e.g., browser, password managers) from auto-filling form fields. Based on the autocomplete HTML attribute. |

### Guidelines
- **DO:** include text inputs when a user should be able to submit any value.
- **DO:** include select inputs when a user should only be able to select from a set of values.
- **DO:** include descriptions and placeholder text to provide context to users.
- **DO:** always position the submit button at the bottom of the form.
- **DON'T:** include a form without a submit button.

---

## Input

The Input component renders a text input field where a user can enter a custom text value. Like other inputs, this component should only be used within a Form that has a submit button.

### Example
```jsx
import { useState } from 'react';
import { Form, Input } from '@hubspot/ui-extensions';

const Extension = () => {
  const [name, setName] = useState('');
  const [validationMessage, setValidationMessage] = useState('');
  const [isValid, setIsValid] = useState(true);

  return (
    <Form>
      <Input
        label="First Name"
        name="first-name"
        tooltip="Please enter your first name"
        description="Please enter your first name"
        placeholder="First name"
        required={true}
        error={!isValid}
        validationMessage={validationMessage}
        onChange={(value) => {
          setName(value);
        }}
        onInput={(value) => {
          if (value !== 'Bill') {
            setValidationMessage('This form only works for people named Bill');
            setIsValid(false);
          } else if (value === '') {
            setValidationMessage('First name is required');
            setIsValid(false);
          } else {
            setValidationMessage('Valid first name!');
            setIsValid(true);
          }
        }}
      />
      <Input
        label="Password"
        name="password"
        description="Enter your password"
        placeholder="Password"
        onInput={() => {}}
        type="password"
      />
    </Form>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| name | String | The input's unique identifier, similar to the HTML input element name attribute. |
| label | String | The text that displays above the input. Required if inputType is not set to hidden. |
| required | Boolean | When set to true, displays a required field indicator. |
| value | Function | The value of the input. |
| type | 'text' (default) \| 'password' | The type of input. An input with the 'password' type will hide the characters that the user types. |
| readOnly | Boolean | When set to true, users will not be able to enter a value into the field. |
| description | String | Displayed text that describes the field's purpose. |
| tooltip | String | The text that displays in a tooltip next to the input label. |
| placeholder | String | The text that appears in the input before a value is set. |
| error | Boolean | When set to true, validationMessage is displayed as an error message if provided. The input will also render in an error state so that users are aware. If left false, validationMessage is displayed as a success message. |
| validationMessage | String | The text to show if the input has an error. |
| onChange | (value: string) => void | A callback function that is invoked when the value is committed. Currently, these are onBlur of the input and when the user submits the form. |
| onInput | (value: string) => void | A function that is called and passes the value when the field is edited by the user. Should be used for validation. It's recommended that you don't use this value to update state (use onChange instead). |
| onBlur | (value: string) => void | A function that is called and passes the value when the field loses focus. |
| onFocus | (value: string) => void | A function that is called and passed the value when the field gets focused. |

### Guidelines
- **DO:** make label and description text concise and clear.
- **DO:** include placeholder text to help users understand what's expected in the field.
- **DO:** indicate if a field is required.
- **DO:** include clear validation error messages so that users know how to fix errors.
- **DON'T:** use this component for long responses, such as open-ended comments or feedback. Instead, use the TextArea component.
- **DON'T:** use placeholder text for critical information, as it will disappear once users begin to type. Critical information should be placed in the label and descriptive text, with additional context in the tooltip if needed.

---

## NumberInput

The NumberInput component renders a number input field. Commonly used within the Form component.

### Example
```jsx
import { NumberInput } from '@hubspot/ui-extensions';

const Extension = () => {
  const [portalCount, setPortalCount] = useState(0);
  return (
    <NumberInput
      label={'HubSpot Portal Count'}
      name="portalsNumber"
      description={'Number of active portals'}
      placeholder={'number of portals'}
      value={portalCount}
      onChange={(value) => setPortalCount(value)}
    />
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| name | String | The input's unique identifier. |
| label | String | The text that displays above the dropdown menu. |
| value | String \| number | The value of the input. |
| defaultValue | Number | The value of the input on initial render. |
| description | String | Text that describes the field's purpose. |
| required | Boolean | When set to true, displays a required field indicator. |
| readOnly | Boolean | When set to true, users will not be able to enter a value into the field. Set to false by default. |
| placeholder | String | The text that appears in the input before a value is set. |
| tooltip | String | The text that displays in a tooltip next to the label. |
| error | Boolean | When set to true, validationMessage is displayed as an error message if provided. The input will also render its error state to let the user know there's an error. When false (default), validationMessage is displayed as a success message. |
| validationMessage | String | The text to display if the input has an error. |
| min | Number | Sets the lower bound of the input. |
| max | Number | Sets the upper bound of the input. |
| precision | Number | Sets the number of digits to the right of the decimal point. |
| formatStyle | 'decimal' \| 'percentage' | Formats the input as a decimal or percentage. |
| onBlur | (value: number) => void | A function that is called every time the field loses focus, passing the value. |
| onChange | (value: number) => void | A callback function that is invoked when the value is committed. Currently these times are onBlur of the input and when the user submits the form. |
| onFocus | (value: number) => void | A function that is called every time the field gets focused on, passing the value. |

### Guidelines
- **DO:** make label and description text concise and clear.
- **DO:** include placeholder text to help users understand what's expected in the field.
- **DO:** indicate if there is a minimum or maximum number requirement.
- **DO:** indicate if a field is required.
- **DO:** include clear validation error messages so that users know how to fix errors.
- **DON'T:** use this component for long responses, such as open-ended comments or feedback. Instead, use the TextArea component.
- **DON'T:** use placeholder text for critical information, as it will disappear once users begin to type. Critical information should be placed in the label and descriptive text, with additional context in the tooltip if needed.

---

## Select

The Select component renders a dropdown menu select field where a user can select a single value. A search bar will be automatically included when there are more than seven options.

### Example
```jsx
import { Select } from '@hubspot/ui-extensions';

const Extension = () => {
  const [name, setName] = useState(null);
  const [validationMessage, setValidationMessage] = useState('');
  const [isValid, setIsValid] = useState(true);

  const options = [
    { label: 'Bill', value: 42 },
    { label: 'Ted', value: 43 },
  ];

  return (
    <Form>
      <Select
        label="Best Bill & Ted Character?"
        name="best-char"
        tooltip="Please choose"
        description="Please choose"
        placeholder="Bill or Ted?"
        required={true}
        error={!isValid}
        validationMessage={validationMessage}
        onChange={(value) => {
          setName(value);
          if (!value) {
            setValidationMessage('This is required');
            setIsValid(false);
          } else {
            setValidationMessage('Excellent!');
            setIsValid(true);
          }
        }}
        options={options}
      />
    </Form>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| name | String | The input's unique identifier. |
| label | String | The text that displays above the input. |
| options | Array | The options to display in the dropdown menu. label will be used as the display text, and value should be the option's unique identifier, which is submitted with the form. |
| value | String \| number \| boolean | The value of the input. |
| variant | input (default) \| transparent | The visual style of the button |
| required | Boolean | When set to true, displays a required field indicator. Default is false. |
| readOnly | Boolean | When set to true, users will not be able to fill the input field. Default is false. |
| tooltip | String | The text that displays in a tooltip next to the label. |
| description | String | Text that describes the field's purpose. |
| error | Boolean | When set to true, validationMessage is displayed as an error message if provided. The input will also render its error state to let the user know there's an error. If left false (default), validationMessage is displayed as a success message. |
| validationMessage | String | The text to display if the input has an error. |
| onChange | (value: string) => void | A callback function that is invoked when the value is committed. |
| onInput | (value: string) => void | A callback function that is called and passed the value every time the search field is edited by the user. Prefer updating state in onChange as it fires less frequently, and if you need to update state here, consider debouncing your function. |

### Variants
Using the variant prop, you can set the input to be one of two styles:
- **input (default)**: a standard dropdown menu.
- **transparent**: a hyperlink dropdown menu.

### Guidelines
- **DO:** make label and description text concise and clear.
- **DO:** indicate if a field is required.
- **DO:** include clear validation error messages so that users know how to fix errors.
- **DO:** include placeholder text to help users understand what's expected in the field.
- **DON'T:** use this component when you want users to be able to select multiple options. For multiple options, use the MultiSelect component.
- **DON'T:** use placeholder text for critical information, as it will disappear once users begin to type. Critical information should be placed in the label and descriptive text, with additional context in the tooltip if needed.

---

## Button

The Button component renders a single button. Use this component to enable users to perform actions, such as submitting a form, sending data to an external system, or deleting data. Button text is passed into the component like a standard HTML element, rather than through a prop.

### Example
```jsx
import { Button } from '@hubspot/ui-extensions';

const Extension = () => {
  return (
    <Button
      onClick={() => {
        console.log('Someone clicked the button!');
      }}
      href={{
        url: 'https://wikipedia.org',
        external: true,
      }}
      variant="primary"
      size="md"
      type="button"
    >
      Click me!
    </Button>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| href | Object | Include this prop to open a URL on click. Contains the following fields: url (string): the URL that will open on click. external (boolean): set to true to open the URL in a new tab and display an external link icon. By default: Links to HubSpot app pages will open in the same tab and will not include an icon. Links to non-HubSpot app pages will open in a new tab and include the icon. When a button includes both href and an onClick action, both will be executed on button click. |
| onClick | () => void | A function that will be invoked when the button is clicked. It receives no arguments and it's return value is ignored. |
| disabled | Boolean | When set to true, the button will render in a greyed-out state and cannot be clicked. |
| variant | 'primary' \| 'secondary' (default) \| 'destructive' \| 'transparent' | Sets the color of the button. See variants section for more information. |
| type | 'button' (default) \| 'reset' \| 'submit' | Sets the role HTML attribute of the button. |
| size | 'xs', 'extra-small' \| 'sm', 'small' \| 'med', 'medium' (default) | The size of the button. |
| overlay | Object | Include a Modal or Panel component in this object to open it as an overlay on click. Learn more about using overlays. |
| truncate | Boolean | When set to true, long button text will be truncated with an ellipsis (...), with the full text displayed in a tooltip on hover. |

### Variants
Using the variant prop, you can set the color of the button:
- **'primary'**: a dark blue button for the most frequently used or most important action on an extension. Each extension should only have one primary button.
- **'secondary'**: a grey button to provide alternative or non-primary actions. Each extension should include no more than two secondary buttons.
- **'destructive'**: a red button for actions that delete, disconnect, or perform any action that the user can't undo. Button text should clearly communicate what is being deleted or disconnected. After a destructive button is clicked, the user should have to verify or confirm the action.
- **'transparent'**: a button with the background and border color removed, styled like a hyperlink.

### Guidelines
- **DO:** set button text that clearly communicates what action will occur when a user clicks it. Text should be unambiguous and concise (~2-4 words).
- **DO:** use sentence-casing for button text (only the first word capitalized).
- **DO:** minimize the number of buttons that appear on a page record across all extensions.
- **DO:** always open links to pages outside of the HubSpot app in a new tab (external: true).
- **DON'T:** include multiple primary buttons in a single extension.
- **DON'T:** use a destructive button unless the consequences are significant or irreversible.

---

## DateInput

The DateInput component renders an input field where a user can select a date.

### Example
```jsx
import React, { useState } from 'react';
import { Flex, DateInput } from '@hubspot/ui-extensions';

function RemoteApp() {
  const [dateValue, setDateValue] = useState(null);

  return (
    <Flex direction="column">
      <DateInput
        label="Appointment Date Partially Controlled"
        name="date"
        onChange={(value) => {
          setDateValue(value);
        }}
        value={dateValue}
        format="ll"
      />

      <DateInput
        label="Appointment Date Uncontrolled"
        name="appointment-date"
        format="LL"
      />
    </Flex>
  );
}
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| name | String | The input's unique identifier. |
| label | String | The text that displays above the input. |
| value | Object | The value of the input. Must include the year, month, and day: `{ year: number; month: number; date: number }` where year is the four-digit year (e.g., 2023), month starts at 0 (0 = January, 11 = December), and date is the day number (e.g., 1 = first day of month). |
| defaultValue | Object | The default date value. Uses the same format as the value field. |
| required | Boolean | When set to true, displays a required field indicator. |
| tooltip | String | The text that displays in a tooltip next to the label. |
| readOnly | Boolean | When set to true, the checkbox cannot be selected. |
| description | String | Text that describes the field's purpose. |
| error | Boolean | When set to true, validationMessage is displayed as an error message. The input will render its error state. If false (default), validationMessage is displayed as a success message. |
| validationMessage | String | The text to display if the input has an error. |
| min | Object | Sets the earliest valid date available using format: `{ year: number; month: number; date: number }` |
| max | Object | Sets the latest valid date available using format: `{ year: number; month: number; date: number }` |
| minValidationMessage | String | Message displayed when users hover over dates before the min date. |
| maxValidationMessage | String | Message displayed when users hover over dates after the max date. |
| format | 'short' (default) \| 'long' \| 'medium' \| 'standard' \| 'YYYY-MM-DD' \| L \| LL \| ll | The date format. Options: short (09/04/1986), long (September 4, 1986), medium (Sep 4, 1986), standard (1986-09-04), YYYY-MM-DD (1986-09-04), L (09/04/1986), LL (September 4, 1986), ll (Sep 4, 1986). |
| clearButtonLabel | String | Sets the label of the button that clears the date. |
| todayButtonLabel | String | Sets the label of the button that inserts today's date. |
| timezone | 'userTz' (default) \| 'portalTz' | Sets the timezone for calculating valid dates. userTz (default): the user's time zone; portalTz: the portal's default time zone. |
| onChange | (checked: boolean, value: string) => void | A callback function invoked when the value is committed. Currently occurs on onBlur and form submit. |
| onBlur | (value: DateInputEventsPayload) => void | A function called when the field loses focus. |
| onFocus | (value: DateInputEventsPayload) => void | A function called when the field gets focused. |

### Guidelines
- Use for date selection in forms
- Set min/max constraints when appropriate for validation
- Provide clear labels and descriptions
- Use appropriate date format for your use case

---

## SearchInput

The SearchInput component renders an input field that enables users to search. The component doesn't provide search functionality out of the box, but includes props for managing input state and validation.

### Example
```jsx
import React, { useState } from 'react';
import {
  Button,
  Flex,
  Form,
  SearchInput,
  Text,
  hubspot,
} from '@hubspot/ui-extensions';

hubspot.extend(({ actions }) => <Extension sendAlert={actions.addAlert} />);

const Extension = ({ sendAlert }) => {
  const [searchValue, setSearchValue] = useState('');

  const handleSubmit = (formData) => {
    const searchTerm = formData.targetValue.search;
    sendAlert({
      message: `You searched for: "${searchTerm}"`,
      type: 'success',
    });
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Flex direction="column" gap="md">
        <SearchInput
          name="search"
          label="Search"
          placeholder="Enter your search term"
          value={searchValue}
          onChange={(value) => setSearchValue(value)}
        />
        <Button type="submit">Search</Button>
        {searchValue && <Text>Current search: {searchValue}</Text>}
      </Flex>
    </Form>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| label | String | The label text to display for the input. |
| name | String | The unique identifier for the input. |
| value | String | The value of the input. |
| placeholder | String | Text that appears in the input when it has no value set. |
| tooltip | String | Text that will appear in a tooltip on hover next to the input label. |
| required | Boolean | When set to true, displays a required field indicator. |
| readOnly | Boolean | When set to true, the field is not editable. |
| description | String | Instructional message to help understand the purpose of the input. |
| error | Boolean | When set to true, renders the error state and shows validationMessage as an error. |
| validationMessage | String | The text to show under the input for error or success validations. Will appear below the input. |
| getValidationMessage | (value: string) => string \| null | Called to validate the input value and display a validation message. |
| onChange | (value: string) => void | A callback function that is invoked when the input value changes. |
| onInput | (value: string) => void | A callback function that is invoked every time the field is edited by the user. |
| onBlur | (value: string) => void | A function that is called when the field loses focus. |
| onFocus | (value: string) => void | A function that is called when the field gets focused. |
| clearable | Boolean | When set to true, shows a clear button to clear the input. Default is true. |

### Guidelines
- Use for search functionality in tables or lists
- Include clear placeholder text
- Provide feedback when search returns no results

---

## TextArea

The TextArea component renders a multi-line text input field. Use this component for longer text responses, such as comments, descriptions, or feedback.

### Example
```jsx
import React, { useState } from 'react';
import { TextArea } from '@hubspot/ui-extensions';

const Extension = () => {
  const [description, setDescription] = useState('');

  return (
    <TextArea
      label="Product Description"
      name="description"
      description="Enter a detailed description of the product"
      placeholder="Type your description here..."
      value={description}
      onChange={(value) => setDescription(value)}
      rows={4}
      maxLength={500}
    />
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| name | String | The input's unique identifier. |
| label | String | The text that displays above the input. |
| value | String | The value of the input. |
| defaultValue | String | The default value of the input on initial render. |
| placeholder | String | The text that appears in the input before a value is set. |
| required | Boolean | When set to true, displays a required field indicator. |
| readOnly | Boolean | When set to true, users will not be able to edit the field. |
| description | String | Text that describes the field's purpose. |
| tooltip | String | The text that displays in a tooltip next to the label. |
| error | Boolean | When set to true, validationMessage is displayed as an error message. The input will render its error state. If false (default), validationMessage is displayed as a success message. |
| validationMessage | String | The text to display if the input has an error. |
| maxLength | Number | Sets the maximum number of characters allowed in the input. |
| rows | Number | Sets the number of visible text rows. Default is 3. |
| cols | Number | Sets the visible width of the text area in characters. |
| resize | 'none' \| 'both' \| 'horizontal' \| 'vertical' (default) | Controls whether and how users can resize the text area. |
| onChange | (value: string) => void | A callback function invoked when the value is committed (onBlur and form submit). |
| onInput | (value: string) => void | A callback function invoked every time the field is edited by the user. |
| onBlur | (value: string) => void | A function called when the field loses focus. |
| onFocus | (value: string) => void | A function called when the field gets focused. |

### Guidelines
- **DO:** use TextArea for long-form text input (comments, descriptions, feedback)
- **DO:** set an appropriate number of rows based on expected content length
- **DO:** provide maxLength when there's a character limit
- **DO:** include clear placeholder text to guide users
- **DON'T:** use TextArea for short, single-line inputs (use Input instead)
- **DON'T:** make the text area too small for the expected content

---

## ToggleGroup

The ToggleGroup component renders a group of checkboxes or radio buttons for selecting one or multiple options. Use this component when you want users to select from a predefined set of options.

### Example
```jsx
import React, { useState } from 'react';
import { ToggleGroup } from '@hubspot/ui-extensions';

const Extension = () => {
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [selectedShipping, setSelectedShipping] = useState('');

  return (
    <>
      {/* Checkbox list for multiple selections */}
      <ToggleGroup
        name="documents"
        label="Required Documents"
        description="Select all documents that apply"
        toggleType="checkboxList"
        value={selectedDocuments}
        onChange={(value) => setSelectedDocuments(value)}
        options={[
          { label: "Certificate of Origin", value: "origin" },
          { label: "Health Certificate", value: "health" },
          { label: "Insurance", value: "insurance" }
        ]}
      />

      {/* Radio button list for single selection */}
      <ToggleGroup
        name="shipping-method"
        label="Shipping Method"
        toggleType="radioButtonList"
        value={selectedShipping}
        onChange={(value) => setSelectedShipping(value)}
        options={[
          { label: "Air Freight", value: "air" },
          { label: "Sea Freight", value: "sea" },
          { label: "Land Transport", value: "land" }
        ]}
        required={true}
      />
    </>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| name | String | The input's unique identifier. |
| label | String | The text that displays above the toggle group. |
| toggleType | 'checkboxList' \| 'radioButtonList' | The type of toggles to display. checkboxList: allows multiple selections; radioButtonList: allows single selection. |
| options | Array | An array of options. Each option is an object with label (string) and value (string \| number \| boolean). |
| value | String \| Number \| Boolean \| Array | The selected value(s). For checkboxList, this should be an array. For radioButtonList, this should be a single value. |
| defaultValue | String \| Number \| Boolean \| Array | The default selected value(s) on initial render. |
| required | Boolean | When set to true, displays a required field indicator. |
| readOnly | Boolean | When set to true, users cannot change the selection. |
| description | String | Text that describes the field's purpose. |
| tooltip | String | The text that displays in a tooltip next to the label. |
| error | Boolean | When set to true, validationMessage is displayed as an error message. If false (default), validationMessage is displayed as a success message. |
| validationMessage | String | The text to display if the input has an error. |
| onChange | (value: string \| string[]) => void | A callback function invoked when the selection changes. For checkboxList, receives an array of selected values. For radioButtonList, receives a single value. |

### Toggle Types
- **checkboxList**: Displays a list of checkboxes. Users can select multiple options. The value prop should be an array.
- **radioButtonList**: Displays a list of radio buttons. Users can select only one option. The value prop should be a single value.

### Guidelines
- **DO:** use checkboxList when users can select multiple options
- **DO:** use radioButtonList when users must select exactly one option
- **DO:** provide clear, concise labels for each option
- **DO:** use description to explain the purpose of the selection
- **DON'T:** include too many options (consider Select for more than 7-8 options)
- **DON'T:** use toggles for yes/no questions (use a single Checkbox instead)

---

## ButtonRow

The ButtonRow component renders a row of specified Button components. Use this component when you want to include multiple buttons in a row.

When the number of included buttons exceeds the available space, the extra buttons will be presented as a Dropdown style button.

### Example
```jsx
import { Button, ButtonRow } from '@hubspot/ui-extensions';

const Extension = () => {
  return (
    <ButtonRow disableDropdown={false}>
      <Button
        onClick={() => {
          console.log('Regular button clicked');
        }}
      >
        Regular Button
      </Button>
      <Button
        onClick={() => {
          console.log('Reset button clicked');
        }}
        variant="destructive"
        type="reset"
      >
        Reset
      </Button>
      <Button
        onClick={() => {
          console.log('Submit button clicked');
        }}
        variant="primary"
        type="submit"
      >
        Submit
      </Button>
    </ButtonRow>
  );
};
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| disableDropdown | Boolean | By default, when the number of buttons exceeds the available horizontal space, the extra buttons will collapse into a single dropdown menu button. Set this prop to true to prevent the dropdown button from being interacted with. Default is false. |
| dropDownButtonOptions | Object | When the included buttons exceed the available space, use this prop to customize the dropdown button. Object can contain: size ('xs', 'sm', 'md'), text (button text, default 'More'), variant ('primary', 'secondary', 'transparent'). |

### Guidelines
- **DO:** include a secondary button with a destructive button to allow users to cancel the action.
- **DON'T:** use multiples of the same button type in a row.
- **DON'T:** use more than two secondary buttons in a single extension.
- **DON'T:** use more than three buttons in a row.

---

## Table

The Table component renders a table for displaying and organizing data. Use the following subcomponents to format the table:
- **TableHead**: the header section containing column labels
- **TableRow**: individual table rows
- **TableHeader**: cells containing bolded column labels
- **TableBody**: container for the main table contents
- **TableCell**: individual cells within the main body
- **TableFooter**: a row at the bottom to summarize columns

### Example
```jsx
import {
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
} from '@hubspot/ui-extensions';

const Extension = () => {
  return (
    <Table bordered={true} paginated={true} pageCount="5">
      <TableHead>
        <TableRow>
          <TableHeader width="min">Name</TableHeader>
          <TableHeader width="min">Role</TableHeader>
        </TableRow>
      </TableHead>
      <TableBody>
        <TableRow>
          <TableCell width="min">Tim Robinson</TableCell>
          <TableCell width="min">Driver's Ed. Instructor</TableCell>
        </TableRow>
        <TableRow>
          <TableCell width="min">Patti Harrison</TableCell>
          <TableCell width="min">Tables (vendor)</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
};
```

### Props

**Table Props:**
| Prop | Type | Description |
|------|------|-------------|
| bordered | Boolean | When set to false, the table will not include borders. Default is true. |
| flush | Boolean | When set to true, the table will not include bottom margin. Default is false. |
| paginated | Boolean | When set to true, the table will include pagination navigation. Default is false. |

**TableHeader Props:**
| Prop | Type | Description |
|------|------|-------------|
| align | 'center' \| 'left' \| 'right' | Sets the alignment of a table header. |
| sortDirection | 'none' \| 'ascending' \| 'descending' \| 'never' | A visual indicator of the current direction in which the column is sorted. Does not modify the table data. |
| width | Number \| 'min' \| 'max' \| 'auto' | Sets the width of a table header. min: content width only; max: maximum available width; auto: adjusts based on available space. |

**TableCell Props:**
| Prop | Type | Description |
|------|------|-------------|
| align | 'center' \| 'left' \| 'right' | Sets the alignment of a table cell. |
| width | Number \| 'min' \| 'max' \| 'auto' | Sets the width of a table cell. |
| colSpan | Number | Sets the number of columns a cell should span. |

### Pagination Props
When `paginated` is set to true, you can use these additional props:
| Prop | Type | Description |
|------|------|-------------|
| maxVisiblePageButtons | Number | The maximum number of page buttons to display. |
| page | Number | Denotes the current page number. |
| pageCount | Number | The total number of pages available. |
| showButtonLabels | Boolean | When set to false, hides the text labels for First/Prev/Next buttons. Default is true. |
| showFirstLastButtons | Boolean | When set to true, displays the First/Last page buttons. Default is false. |
| onPageChange | (pagenumber: number) => void | A function that is invoked when the page pagination button is clicked. |

### Guidelines
- **DO:** keep text within data cells clear and concise for easier scanning.
- **DO:** always include a table header row to label columns.
- **DO:** limit the use of links in table cells.
- **DO:** use button size 'xs' and 'secondary' variant for row actions, right-aligned.
- **DON'T:** use multiple tables on one screen when possible.
- **DON'T:** render a blank table if there's no data. Use EmptyState component instead.
- **DON'T:** overwhelm users with too much information in table cells.

---

## Design Patterns

### Form Design Patterns

Use forms to enable users to submit data to HubSpot or an external system. Follow these patterns to keep your app card consistent with HubSpot's designs.

#### Field Organization
- **DO:** Stack form fields vertically. Most people are used to vertical scroll and may not have wide enough screens for horizontal layouts.
- **DO:** Include only one input per line as a general principle.
- **DON'T:** Make forms too long. If stacking vertically makes the card too long, break the form into multiple steps.

#### Buttons
- **DO:** Always include a submit button with each form.
- **DO:** For multi-step forms, include a "Next" button at the bottom of each step to guide users to the next step.
- **DO:** Use the last step to end with a submit button.
- **DO:** Position buttons at the bottom of the form.
- **Pattern:** In multi-step forms, the Primary Button should appear to the left of the Secondary Button, and both should be left-aligned.

#### Multi-Step Forms Best Practices
```jsx
// Example pattern for multi-step navigation
<ButtonRow>
  {formStep < totalSteps - 1 && (
    <Button variant="primary" onClick={nextStep}>
      Next
    </Button>
  )}
  {formStep === totalSteps - 1 && (
    <Button type="submit" variant="primary">
      Submit
    </Button>
  )}
  <Button variant="secondary" onClick={cancel}>
    Cancel
  </Button>
</ButtonRow>
```

#### Validation
- **DO:** Include clear validation error messages so users know how to fix errors.
- **DO:** Indicate if a field is required.
- **DO:** Provide immediate feedback when validation fails.

---

### Table Design Patterns

Use Table components to render tables for displaying sets of data that are too detailed or complicated to be described with text only, or when users need to compare data sets.

#### Buttons in Tables
- **DO:** Include a button in a row only if there's an action directly associated with that row.
- **DO:** Use the `xs` button size and `secondary` variant for row actions.
- **DO:** Keep table row buttons right-aligned to the information they relate to.
- **Pattern:** This enables users to read information from left to right, then decide to take action.

Example:
```jsx
<TableRow>
  <TableCell>{data}</TableCell>
  <TableCell width="min">
    <Button size="xs" variant="secondary" onClick={action}>
      Action
    </Button>
  </TableCell>
</TableRow>
```

#### Content Guidelines
- **DON'T:** Overwhelm users with too much information in table cells.
- **DO:** Use a Panel that can be opened from the row for long-form content.
- **DO:** Keep table cell content concise to prevent crowding.

#### Empty States
- **DON'T:** Render a blank table when there's no data to display.
- **DO:** Use the EmptyState component when filters or searches return no results.

#### Row Actions with Destructive Buttons
When using destructive buttons (delete, disconnect, etc.) in table rows:
- **DO:** Use the `destructive` variant.
- **DO:** Clearly communicate what will be deleted in the button text.
- **Pattern:** Consider adding a confirmation step before executing destructive actions.

---

## Implementation Checklist

### For Forms:
- [ ] Fields are stacked vertically
- [ ] Only one input per line
- [ ] Submit button is included
- [ ] Required fields are indicated
- [ ] Validation messages are clear
- [ ] Multi-step forms have navigation buttons (Next/Previous)
- [ ] Primary button appears before Secondary button in ButtonRow

### For Tables:
- [ ] Table headers are always included
- [ ] Row action buttons use size="xs" and variant="secondary"
- [ ] Action buttons are right-aligned in their column
- [ ] Destructive actions use variant="destructive"
- [ ] Empty states are handled with EmptyState component, not blank tables
- [ ] Table cell content is concise

---

## Statistics

The Statistics component renders a visual spotlight of one or more data points. Includes the StatisticsItem and StatisticsTrend subcomponents.

### Example
```jsx
import {
  Statistics,
  StatisticsItem,
  StatisticsTrend,
} from '@hubspot/ui-extensions';

const Extension = () => {
  return (
    <Statistics>
      <StatisticsItem label="Item A Sales" number="10000">
        <StatisticsTrend direction="decrease" value="200%" />
      </StatisticsItem>
      <StatisticsItem label="Item B Sales" number="100000">
        <StatisticsTrend direction="increase" value="100%" />
      </StatisticsItem>
    </Statistics>
  );
};
```

### Props

**StatisticsItem Props:**
| Prop | Type | Description |
|------|------|-------------|
| id | String | The statistic item's unique identifier. |
| label | String | The item's label. |
| number | String \| Number | The string to be displayed as the item's primary number. |

**StatisticsTrend Props:**
| Prop | Type | Description |
|------|------|-------------|
| direction | 'increase' (default) \| 'decrease' | The direction of the trend arrow. |
| value | String | The text to be displayed as the trend value. |
| color | 'red' \| 'green' | The color of the trend arrow. |

### Variants

In StatisticsTrend components, use the direction prop to describe whether data is trending upwards or downwards:
- **increase**: for additions or positive progression for a given time period
- **decrease**: for subtractions or negative progression for a given time period

Note that the positive or negative movement is intended solely to represent increase or decrease in numerical value. Be mindful of how these movements can communicate sentiment. For example, a decrease in support volume can be a net positive, which can be confusing when represented by a red, downward arrow.

### Usage Examples
- Calling out the progress of quarterly sales for a company
- Monitoring traffic and social media engagement for a contact for the month

### Guidelines
- **DO:** keep statistics labels short and concise
- **DO:** place statistics components towards the top of a card when possible to enable users to more easily scan information without scrolling
- **DON'T:** include more than three statistics components per card if possible
- **DON'T:** use more than four statistics components side by side
- **DON'T:** include sensitive data that you don't want all users to see

---

## StepIndicator

The StepIndicator component renders an indicator to show the current step of a multi-step process.

### Example
```jsx
import { Flex, Box, StepIndicator, Button } from '@hubspot/ui-extensions';

hubspot.extend(() => <Extension />);

function Extension() {
  const [currentStep, setCurrentStep] = useState(0);

  return (
    <Flex direction="column" gap="md">
      <StepIndicator
        currentStep={currentStep}
        stepNames={['First', 'Second', 'Third']}
      />
      <Box>
        <Button onClick={() => setCurrentStep(currentStep - 1)}>
          Previous
        </Button>
        <Button onClick={() => setCurrentStep(currentStep + 1)}>Next</Button>
      </Box>
    </Flex>
  );
}
```

### Props
| Prop | Type | Description |
|------|------|-------------|
| circleSize | 'xs', 'extra-small' \| 'sm', 'small' (default) \| 'md', 'medium' \| 'lg', 'large' \| 'xl', 'extra-large' | The size of the indicator circles. |
| currentStep | Number | The currently active step. Steps are zero-based, meaning the first step is assigned 0. |
| direction | 'horizontal' (default) \| 'vertical' | The orientation of the indicator. |
| stepNames | Array | An array containing the name of each step. |
| variant | 'flush' \| 'default' (default) \| 'compact' | Sets component spacing. compact: only shows the title of the currently active step; flush: only shows the title of the currently active step and removes left and right margin. |
| onClick | (stepIndex: number) => void | A function invoked when a step in the indicator is clicked. Receives the current step index as argument (zero-based). Use this to update the currently active step. |

### Variants
- By default, the step indicator will be laid out **horizontally**, but you can use the `direction` prop to set the orientation to **vertical**
- You can set the size of the step circles using the `circleSize` prop, ranging from 'xs'/'extra-small' to 'xl'/'extra-large'

### Guidelines
- Use for multi-step processes to show progress
- Keep step names concise (1-2 words)
- Consider using horizontal layout for 3-5 steps, vertical for more steps
- Make steps clickable when users can navigate between them freely
