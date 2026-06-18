import type { ReactNode } from 'react';
import { StyleSheet, Text } from 'react-native';

import { colors, radius, spacing } from '../theme';

type Tone = 'info' | 'ok' | 'danger';

export function Banner({ tone = 'info', children }: { tone?: Tone; children: ReactNode }) {
  const bg = tone === 'ok' ? colors.okBg : tone === 'danger' ? '#FDECEC' : colors.infoBg;
  const color = tone === 'ok' ? colors.ok : tone === 'danger' ? colors.danger : colors.text;
  return <Text style={[styles.box, { backgroundColor: bg, color }]}>{children}</Text>;
}

const styles = StyleSheet.create({
  box: {
    borderRadius: radius.md,
    padding: spacing(3.5),
    fontSize: 14,
    lineHeight: 20,
    overflow: 'hidden',
  },
});
