# Requirements Coverage

## Covered

- Registered organizational users with roles, permissions and departments.
- Backend-enforced RBAC for administrative and content-management operations.
- Global and targeted announcements/events by department, role or user.
- Announcement create, read, update, delete, search, archive filtering, scheduling and expiration.
- Controlled attachments for announcements and events.
- Reactions, comments, comment disabling, acknowledgement and compliance report.
- Pinning and ordered announcement feed.
- Event create, read, update, delete, search and date-range calendar queries.
- Company, Team and My Calendar layers.
- Announcement-to-event link through `announcement_id`.
- RSVP and custom per-user reminders.
- Reminder recalculation on event update and cancellation on cascade deletion.
- Notification inbox for announcement/event lifecycle and due reminders.
- Modular routers, services, schemas and models.
- Database indexes, uniqueness constraints, pagination and bounded uploads.
- Alembic migrations, Docker deployment files and integration tests.
- Arabic RTL React frontend for authentication, dashboard, announcements, calendar, notifications and administration.
- Responsive desktop/mobile layout with role-aware actions and automatic access-token refresh.
- Frontend audience selection for global or targeted announcements and events.

## Integration points intentionally external

- HTTPS termination belongs at the reverse proxy or cloud load balancer.
- Login/upload rate limiting belongs in the API gateway or Redis-backed limiter.
- Email, mobile push and WebSocket delivery consume the internal notifications table.
- Antivirus scanning should run in the object-storage upload pipeline.
- Redis caching can be added for high-volume public feeds after production traffic is measured.

These are deployment integrations rather than missing domain logic. The internal notification and attachment records provide stable extension points for them.
