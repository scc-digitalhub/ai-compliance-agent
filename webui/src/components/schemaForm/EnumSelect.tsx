import { Autocomplete, Chip, MenuItem, TextField } from "@mui/material";
import { enumLabel } from "./fieldHelpers";

interface EnumSelectProps {
  label: string;
  options: string[];
  value: string | undefined;
  onChange: (value: string) => void;
  required?: boolean;
  helperText?: string;
}

export function EnumSelect({ label, options, value, onChange, required, helperText }: EnumSelectProps) {
  return (
    <TextField
      select
      fullWidth
      size="small"
      label={label}
      required={required}
      value={value ?? ""}
      helperText={helperText}
      onChange={(e) => onChange(e.target.value)}
    >
      {options.map((option) => (
        <MenuItem key={option} value={option}>
          {enumLabel(option)}
        </MenuItem>
      ))}
    </TextField>
  );
}

interface MultiEnumSelectProps {
  label: string;
  options: string[];
  value: string[];
  onChange: (value: string[]) => void;
  helperText?: string;
}

export function MultiEnumSelect({ label, options, value, onChange, helperText }: MultiEnumSelectProps) {
  return (
    <Autocomplete
      multiple
      size="small"
      options={options}
      value={value}
      getOptionLabel={(option) => enumLabel(option)}
      onChange={(_e, newValue) => onChange(newValue)}
      renderTags={(tagValue, getTagProps) =>
        tagValue.map((option, index) => {
          const { key, ...rest } = getTagProps({ index });
          return <Chip size="small" label={enumLabel(option)} key={key} {...rest} />;
        })
      }
      renderInput={(params) => <TextField {...params} label={label} helperText={helperText} />}
    />
  );
}
