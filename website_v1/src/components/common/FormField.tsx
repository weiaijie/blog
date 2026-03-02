type FormFieldProps = {
  label: string;
  name: string;
  type?: 'text' | 'email';
  required?: boolean;
};

export function FormField({
  label,
  name,
  type = 'text',
  required = false
}: FormFieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <input name={name} type={type} required={required} />
    </label>
  );
}
