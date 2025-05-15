# SSL Certificates

This directory contains SSL certificates for secure communication between services.

## Certificate Generation

### Development Certificates
For local development, generate a self-signed certificate using OpenSSL:

```bash
# Create certificates directory if it doesn't exist
mkdir -p certs

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/wildcard.key \
  -out certs/wildcard.crt \
  -subj "/CN=*.localhost" \
  -addext "subjectAltName=DNS:*.localhost,DNS:localhost"
```

### Production Certificates
TODO
Use a proper SSL certificate from a trusted CA (like Let's Encrypt).

## Certificate Files

- `wildcard.crt`: Public certificate file
- `wildcard.key`: Private key file

## Security Notes

1. Never commit the private key (`wildcard.key`) to version control
2. Keep the private key secure and restrict access
3. Regularly rotate certificates in production
4. Use different certificates for different environments

## Adding to Trust Store (Development)

### Windows
```powershell
# Import certificate to trusted root
Import-Certificate -FilePath "certs/wildcard.crt" -CertStoreLocation Cert:\LocalMachine\Root
```

### Linux
```bash
# Copy certificate to trusted store
sudo cp certs/wildcard.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### macOS
```bash
# Import certificate to keychain
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/wildcard.crt
```

## Troubleshooting

If you encounter SSL errors:
1. Verify certificate paths in `docker-compose.yml`
2. Check certificate permissions
3. Ensure the certificate is in the trust store
4. Verify the certificate hasn't expired
