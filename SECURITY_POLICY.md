# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in RUIE, please report it responsibly.

### DO NOT

- Open a public issue on GitHub
- Post details in discussions or forums
- Share the vulnerability publicly before a fix is available

### DO

**Report privately using GitHub's Security Advisory feature:**
1. Go to the [Security tab](https://github.com/Elegius/RUIE/security)
2. Click "Report a vulnerability"
3. Provide detailed information about the vulnerability

**Or email the maintainers** (check MAINTAINERS.md for contact information)

## Vulnerability Disclosure

We follow responsible disclosure practices:

- **Initial Response**: Within 48 hours
- **Assessment**: Within 1 week
- **Fix Development**: Within 2 weeks (or status update provided)
- **Public Disclosure**: After patch is released (typically 30-90 days)

## Security Standards

RUIE implements the following security controls:

### Code Security
- ✅ No eval() or exec() usage
- ✅ No hardcoded secrets or credentials
- ✅ Input validation on all user inputs
- ✅ Output encoding to prevent XSS
- ✅ Path traversal prevention
- ✅ Safe subprocess execution (no shell=True)

### Dependency Security
- ✅ Regular dependency updates
- ✅ GitHub Dependabot enabled
- ✅ All dependencies are mature, well-maintained libraries
- ✅ No unused dependencies

### Runtime Security
- ✅ Debug mode disabled in production
- ✅ CORS restricted to localhost only
- ✅ Security headers configured
- ✅ Admin privileges enforced for system operations

### Data Protection
- ✅ No sensitive data logged
- ✅ User data stored locally only
- ✅ No external network calls except to RSI Launcher
- ✅ No telemetry or tracking

## Supported Versions

Security updates are provided for:

| Version | Status | Security Updates |
|---------|--------|------------------|
| 0.2.x   | Current | ✅ Supported |
| 0.1.x   | Obsolete | ⚠️ Limited support |

## Security Checklist for Releases

Before each release:

- [ ] Run full test suite
- [ ] Update all dependencies
- [ ] Review all code changes for security issues
- [ ] Run static security analysis (bandit, safety)
- [ ] Check for new CVEs in dependencies
- [ ] Verify debug mode is disabled
- [ ] Test on clean Windows system
- [ ] Code sign executable (if applicable)
- [ ] Create security changelog section
- [ ] Notify users of any security fixes

## Known Limitations

RUIE is designed for **local desktop use only** and has these limitations:

- **Single-user**: No multi-user authentication system
- **Local storage**: User data not encrypted on disk
- **Requires admin**: Cannot function without elevated privileges
- **Windows-only**: No support for macOS/Linux
- **Not for network exposure**: Should never be exposed to untrusted networks

## Security Advisories

### Current Status

✅ **No known security vulnerabilities**

Last security audit: February 2026

### Historical Advisories

*None currently*

## Dependencies

RUIE uses only well-maintained, security-audited dependencies:

- **PyQt5** (5.15.0+) - Desktop UI framework
- **PyQtWebEngine** (5.15.0+) - Chromium-based web rendering
- **Flask** (3.0.0+) - Web framework
- **Flask-CORS** (4.0.0+) - CORS support
- **Waitress** (2.1.0+) - Production WSGI server

All versions specified in requirements.txt are secure and up-to-date.

## Security Monitoring

We monitor for vulnerabilities through:

- GitHub Dependabot alerts
- Python Safety checks
- Bandit static analysis
- Manual code review
- Community reports

## Questions?

For non-security questions, please:
- Open an issue on GitHub
- Start a discussion
- Check existing documentation

For security questions, follow the reporting procedures above.

---

**Last Updated**: February 4, 2026  
**Status**: ✅ No known vulnerabilities  
**Next Review**: Quarterly (or as needed)