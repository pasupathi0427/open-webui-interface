# Tool credentials export

Copies the username and password a user saves in a tool's user valves (for example their COSEC ESS login) to a table that another application can read with a select-only database user.

The export is **off by default**. It runs only when both variables below are set and the app database is PostgreSQL.

## What gets written

Table `integration.user_tool_credentials`, in its own schema:

| Column           | Content                                                                   |
| ---------------- | ------------------------------------------------------------------------- |
| `user_id`      | One UI user ID                                                            |
| `tool_id`      | Tool ID, e.g. `cosec_attendance`                                        |
| `user_email`   | One UI user's email                                                       |
| `username`     | The username valve, in plain text                                         |
| `password_enc` | The password valve, Fernet-encrypted with `TOOL_CREDENTIALS_EXPORT_KEY` |
| `updated_at`   | Unix time of the last change                                              |

The primary key is (`user_id`, `tool_id`).

- **Save:** saving the tool's valves, in Settings → Tools → valves or in the tool's own sign-in steps, inserts or updates the row.
- **Clear:** clearing the username or the password deletes the row.
- **User deleted:** deleting the user in One UI deletes their rows.
- **One UI never reads this table.** It is outside the Alembic migrations, so upstream upgrades don't touch it.
- **Tool deleted:** deleting the tool does not remove its rows. Delete them by hand if needed.

## Settings

| Variable                        | Example                                            | Meaning                                                                                    |
| ------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `TOOL_CREDENTIALS_EXPORT`     | `cosec_attendance:cosec_username:cosec_password` | `tool_id:username_field:password_field`, comma-separated for several tools. Empty = off. |
| `TOOL_CREDENTIALS_EXPORT_KEY` | (44-character Fernet key)                          | Shared only with the reading app. Never reuse `WEBUI_SECRET_KEY`.                        |

Generate a key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

If `TOOL_CREDENTIALS_EXPORT` is set but the key is missing or invalid, One UI refuses to start and says why.

## Turning it on

1. Add both variables to `.env` and restart One UI. The log shows `Tool credentials export enabled for: cosec_attendance`, and the table is created.
2. Copy the credentials users saved earlier (one time):

   ```bash
   docker compose -f docker-compose.sso.yaml exec open-webui python scripts/export_tool_credentials.py
   ```

   The script decrypts the stored valves, so it must run with the same `WEBUI_SECRET_KEY` as One UI. Running it inside the One UI container guarantees that.
3. Create the read-only user (as the Postgres owner):

   ```sql
   CREATE ROLE cosec_reader LOGIN PASSWORD '<strong password>';
   GRANT USAGE ON SCHEMA integration TO cosec_reader;
   GRANT SELECT ON integration.user_tool_credentials TO cosec_reader;
   ```

   This user can read only this table. It cannot read One UI's tables or write anything.

   The reading app connects to the Postgres service. Inside the compose network the host is `postgres`. From the host machine it is `127.0.0.1:5432`; the port is published on loopback only.

## Reading the password (other app)

Use any Fernet library with the same key. For example, in Python:

```python
from cryptography.fernet import Fernet
password = Fernet(KEY).decrypt(row["password_enc"].encode()).decode()
```

Fernet libraries exist for Java, Node.js, Go and .NET.

## Turning it off

Remove `TOOL_CREDENTIALS_EXPORT` and restart. New saves are no longer copied, and the existing rows stay. To remove them as well:

```sql
DROP SCHEMA integration CASCADE;
```

## After an upstream merge

The export hooks into `update_user_valves_by_id_and_user_id` (`models/tools.py`) and `delete_user_by_id` (`models/users.py`). After merging, save the COSEC valves once and check that `updated_at` changes for your row.
