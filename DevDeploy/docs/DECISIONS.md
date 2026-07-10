# Architecture Decisions

## Decision 001

Use Amazon RDS instead of PostgreSQL Docker container.

Reason

Databases are stateful.

Containers should remain stateless.

Benefits

- Managed backups
- High availability
- Easier recovery
- Better production architecture

---

## Decision 002

Use Terraform modules.

Reason

Reusable infrastructure.

Cleaner code.

Better scalability.

---

## Decision 003

Separate development and production Docker Compose files.

Reason

Production should not mount local source code.

Production images should be immutable.

---

## Decision 004

Use GitHub Actions for CI/CD.

Reason

Native GitHub integration.

Good learning platform.

Simple automation.

---

## Decision 005

Terraform is the only method of provisioning infrastructure.

Reason

Infrastructure must be reproducible.

No manual AWS resource creation.