# Admin Tools

Administrative tools for managing deployed infrastructure.

## Location

```
py/bin/admin
```

## Usage

```bash
py/bin/admin <stage> <command> [subcommand] [options]
```

## Commands

### db - Database Access

Connect to remote PostgreSQL databases through SSH tunnels.

#### Subcommands

**shell / psql** - Open an interactive psql shell

```bash
py/bin/admin production db shell
py/bin/admin staging db psql
```

Requires `psql` to be installed (`brew install postgresql`).

**pgadmin** - Launch pgAdmin in Docker

```bash
py/bin/admin production db pgadmin
py/bin/admin production db pgadmin --port 5435
```

- Starts a pgAdmin container with pre-configured server connection
- Opens browser to `http://localhost:5050`
- Keep the terminal open to maintain the SSH tunnel
- Press Ctrl+C to stop

**tunnel** - Create an SSH tunnel for external clients

```bash
py/bin/admin production db tunnel
py/bin/admin production db tunnel --port 5435
```

Creates a tunnel on `localhost:5434` (or custom port) that forwards to the remote database. Use this with your preferred database client.

Connection details:
- Host: `localhost`
- Port: `5434` (default)
- Database: `postgres`
- Username: `postgres`
- Password: `postgres`

## Options

| Option | Description |
|--------|-------------|
| `--port <port>` | Local port for tunnel/pgadmin (default: 5434) |

## Prerequisites

- **1Password CLI**: Must be authenticated (`op signin`)
- **Terraform**: Infrastructure must be initialized (`bin/iac <stage> init`)
- **psql** (for shell): `brew install postgresql`
- **Docker** (for pgadmin): Docker Desktop running

## How It Works

1. Fetches server IP and SSH key from Terraform outputs
2. Creates an SSH tunnel to the remote PostgreSQL server
3. Connects your client through the tunnel

The script automatically cleans up SSH keys and tunnels on exit.

## Examples

```bash
# Quick database inspection
py/bin/admin production db shell

# Browse with pgAdmin GUI
py/bin/admin production db pgadmin

# Connect with DataGrip or other client
py/bin/admin production db tunnel --port 5435
# Then connect to localhost:5435 in your client
```
