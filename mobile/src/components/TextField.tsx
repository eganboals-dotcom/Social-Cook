import { StyleSheet, Text, TextInput, type TextInputProps, View } from 'react-native';

import { colors, radius, spacing } from '../theme';

export function TextField({
  label,
  style,
  multiline,
  ...props
}: TextInputProps & { label?: string }) {
  return (
    <View style={styles.wrap}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <TextInput
        placeholderTextColor={colors.muted}
        multiline={multiline}
        style={[styles.input, multiline ? styles.multiline : null, style]}
        {...props}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing(1.5) },
  label: { fontSize: 13, fontWeight: '600', color: colors.subtle },
  input: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing(3.5),
    paddingVertical: spacing(3),
    fontSize: 16,
    color: colors.text,
  },
  multiline: { minHeight: 88, textAlignVertical: 'top' },
});
