# Android APK installation and Google Play Protect

## What the warning means

The message “Google Play Protect blocked this app to protect your device” with the explanation that Play Protect has not seen an app from this developer is a reputation / verification warning. It is not the same as an Android minimum-SDK incompatibility message, and it does not by itself prove that the APK contains malware.

The CI artifact named `apolo-charger-debug-apk` is built with the Gradle `debug` variant. Android signs debug builds with a development debug certificate. That certificate is not a verified APOLO publisher identity and does not establish Play Protect reputation.

## What this project does and does not change

- The app targets API 35 and has a minimum API 26. Do not lower target SDK or remove platform protections to try to silence Play Protect.
- Rebuilding the same debug APK, changing its package label, or changing its version does not establish developer reputation.
- A self-created release signing key gives the publisher a stable signing identity, but does not automatically make Google recognize the developer or guarantee that Play Protect stops warning.
- Do not disable Play Protect globally or install a modified APK from an untrusted mirror.

## Recommended distribution path

1. Build a release variant using a publisher-controlled signing key stored securely outside the repository (never commit a keystore or passwords).
2. Verify the APK signature and SHA-256 checksum before distribution.
3. Enroll and verify the publisher identity in Google Play Console.
4. Upload an Android App Bundle to an internal testing track, use Play App Signing, and install it through the official Play testing link. Google Play review and Play Protect decisions remain Google's responsibility.

## If installing a development build

Only use the APK downloaded directly from the project's own GitHub Actions artifact. Verify the artifact source and checksum. If Play Protect still blocks it, do not bypass the protection merely to proceed; use the official Play Console testing route or wait for Google verification/review.

## Current verification boundary

GitHub Actions confirms compilation and unit tests; it cannot certify the APK as malware-free, obtain Google publisher verification, or guarantee installation on every device. A successful CI build is not equivalent to Play Protect approval.
