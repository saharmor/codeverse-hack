# Code Signing and Notarization Setup

## Prerequisites

1. **Apple Developer Account**: Join the Apple Developer Program
2. **Certificates**: Install Developer ID Application certificate in Keychain
3. **App-Specific Password**: Create one for your Apple ID

## GitHub Secrets Setup

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets:

1. **APPLE_CERTIFICATE**
   - Export your Developer ID Application certificate from Keychain as .p12
   - Convert to base64: `base64 -i YourCertificate.p12 | pbcopy`
   - Paste the base64 string as secret value

2. **APPLE_CERTIFICATE_PASSWORD**
   - The password you set when exporting the .p12 certificate

3. **KEYCHAIN_PASSWORD**
   - Any secure password (used for temporary keychain in CI)

4. **APPLE_SIGNING_IDENTITY**
   - Your certificate name, usually: "Developer ID Application: Your Name (TEAM_ID)"
   - Find in Keychain Access → Certificates

5. **APPLE_ID**
   - Your Apple ID email address

6. **APPLE_PASSWORD**
   - App-specific password (not your Apple ID password!)
   - Create at: appleid.apple.com → Sign-In and Security → App-Specific Passwords

7. **APPLE_TEAM_ID**
   - 10-character team ID from Apple Developer account
   - Find at: developer.apple.com → Membership

## Certificate Export Steps

1. Open Keychain Access
2. Find your "Developer ID Application" certificate
3. Right-click → Export
4. Save as .p12 format with a password
5. Convert to base64: `base64 -i certificate.p12 | pbcopy`
6. Add to GitHub secrets as APPLE_CERTIFICATE

## Local Development

For local builds with signing, set these environment variables:

```bash
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"
export APPLE_ID="your-apple-id@example.com"
export APPLE_PASSWORD="your-app-specific-password"
export APPLE_TEAM_ID="YOUR_TEAM_ID"
```

Then build with:
```bash
npm run tauri build
```

## Troubleshooting

- Ensure certificates are properly installed in Keychain
- Verify team ID and signing identity match exactly
- Test app-specific password works with `xcrun altool`
- Check certificate validity period
