---
name: Security Vulnerability
about: Report a security or privacy concern in J.A.N.E.T. Seed
title: "[SECURITY] "
labels: security
assignees: ''

---

## Description
Please provide a clear and detailed description of the security vulnerability or privacy concern.

## Steps to Reproduce
1. 
2. 
3. 

## Impact Assessment
Please check all that apply:
- [ ] Privacy concern (Axiom 9: Sacred Secrets violation)
- [ ] Memory safety (encrypted memory exposure, data leakage)
- [ ] Consent bypass (installation or capability expansion without consent)
- [ ] Constitutional integrity (Axiom 7: Constitution tampering or bypass)
- [ ] Red Thread Protocol failure (Axiom 8: Emergency stop not working)
- [ ] Input validation (potential injection, DoS, or overflow)
- [ ] Authentication/authorization (unauthorized access to Janet or her data)
- [ ] Thread safety (race conditions, data corruption)
- [ ] Encryption weakness (key derivation, storage, or transmission)
- [ ] Resource exhaustion (memory leaks, file handle leaks, connection leaks)
- [ ] Path traversal or file system access issues
- [ ] Network security (if delegation/external services affected)
- [ ] Other (please specify)

## Severity
- [ ] Critical (immediate threat to privacy, safety, or constitutional integrity)
- [ ] High (significant risk, should be addressed quickly)
- [ ] Medium (moderate risk, should be addressed in next release)
- [ ] Low (minor issue, could be addressed with improvements)

## Affected Components
Please check all that apply:
- [ ] Core (`src/core/`)
- [ ] Voice I/O (`src/voice/`)
- [ ] Memory System (`src/memory/`)
- [ ] Delegation Layer (`src/delegation/`)
- [ ] Installation (`src/installer.py`)
- [ ] Constitution (`constitution/`)
- [ ] Entry point (`src/main.py`)
- [ ] Other (please specify):

## Proposed Fix (Optional)
If you have suggestions for how to fix this issue, please describe them here.

## Additional Context
Any other relevant information, screenshots, logs, or code examples that would help understand the issue.

## Responsible Disclosure
- [ ] I understand this is a security issue and will allow time for a fix before public disclosure
- [ ] I have not shared this vulnerability publicly

