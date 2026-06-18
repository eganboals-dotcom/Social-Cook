/**
 * RevenueCat wrapper — loaded lazily and only when configured.
 *
 * If no RevenueCat API key is set (e.g. in Expo Go), IAP is disabled and every
 * call no-ops, so the rest of the app still works. The native module is only
 * required once a key is present (i.e. in a dev/production build).
 */
import { Platform } from 'react-native';
import type { PurchasesPackage } from 'react-native-purchases';

import { REVENUECAT_ANDROID_KEY, REVENUECAT_IOS_KEY } from '../config';

type PurchasesModule = typeof import('react-native-purchases').default;

let purchases: PurchasesModule | null = null;
let available = false;

function load(): PurchasesModule | null {
  if (purchases) return purchases;
  try {
    purchases = require('react-native-purchases').default as PurchasesModule;
  } catch {
    purchases = null;
  }
  return purchases;
}

export function isPurchasesAvailable(): boolean {
  return available;
}

export function configurePurchases(appUserId?: string | null): void {
  const apiKey = Platform.OS === 'android' ? REVENUECAT_ANDROID_KEY : REVENUECAT_IOS_KEY;
  if (!apiKey) return; // IAP disabled when unconfigured (e.g. Expo Go)
  const P = load();
  if (!P) return;
  try {
    P.configure({ apiKey, appUserID: appUserId ?? undefined });
    available = true;
  } catch {
    available = false;
  }
}

export async function setPurchasesUser(appUserId: string): Promise<void> {
  if (!available || !purchases) return;
  try {
    await purchases.logIn(appUserId);
  } catch {
    /* ignore */
  }
}

export async function clearPurchasesUser(): Promise<void> {
  if (!available || !purchases) return;
  try {
    await purchases.logOut();
  } catch {
    /* ignore */
  }
}

export async function getUnlockPackage(): Promise<PurchasesPackage | null> {
  if (!available || !purchases) return null;
  try {
    const offerings = await purchases.getOfferings();
    return offerings.current?.availablePackages[0] ?? null;
  } catch {
    return null;
  }
}

/** Returns true on a completed purchase, false if the user cancelled. */
export async function purchaseUnlock(pkg: PurchasesPackage): Promise<boolean> {
  if (!available || !purchases) {
    throw new Error('In-app purchases are not available in this build.');
  }
  try {
    await purchases.purchasePackage(pkg);
    return true;
  } catch (e) {
    if ((e as { userCancelled?: boolean }).userCancelled) return false;
    throw e;
  }
}

export async function restorePurchases(): Promise<void> {
  if (!available || !purchases) return;
  try {
    await purchases.restorePurchases();
  } catch {
    /* ignore */
  }
}
