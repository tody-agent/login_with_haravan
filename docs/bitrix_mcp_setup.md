# Bitrix24 MCP setup and test guide

This guide covers two different connections:

1. Codex MCP connection to Bitrix24 developer documentation.
2. Bitrix24 portal REST connection to `https://haravan.bitrix24.vn/`.

They are not the same connection. The MCP server is for looking up Bitrix24 REST documentation. The portal webhook is for calling real Haravan Bitrix24 data.

## 1. Codex MCP configuration

Use this MCP server when you want Codex to search Bitrix24 REST API documentation.

### UI configuration

In the Codex MCP configuration screen, enter:

```text
Name
b24-dev-mcp

URL
https://mcp-dev.bitrix24.com/mcp

Bearer token env var
leave empty

Headers
leave empty

Headers from environment variables
leave empty
```

Then click `Save`.

### Terminal command

Run:

```bash
codex mcp add b24-dev-mcp --url https://mcp-dev.bitrix24.com/mcp
```

Check that it is enabled:

```bash
codex mcp list
```

Expected row:

```text
b24-dev-mcp    https://mcp-dev.bitrix24.com/mcp    enabled
```

## 2. Test MCP documentation lookup

After saving the MCP configuration, restart or reconnect Codex if the tools do not appear immediately.

Ask Codex:

```text
Use b24-dev-mcp to search Bitrix24 docs for crm.lead.add.
```

Expected result: Codex should find the Bitrix24 method `crm.lead.add`.

You can also ask:

```text
Use b24-dev-mcp to show parameters for crm.company.get.
```

Expected result: Codex should return REST method details from Bitrix24 docs.

## 3. Haravan Bitrix24 portal webhook

Use this connection when code needs to call real data from:

```text
https://haravan.bitrix24.vn/
```

### Create inbound webhook

In Bitrix24:

```text
Applications -> Developer resources -> Other -> Inbound webhook
```

Grant the needed scopes. For CRM company, lead, deal, and contact APIs, grant:

```text
crm
```

Bitrix24 will generate a URL like:

```text
https://haravan.bitrix24.vn/rest/USER_ID/WEBHOOK_SECRET/
```

Keep this URL secret. Do not commit it to git.

## 4. Local terminal configuration for webhook testing

Set the webhook URL only in your current terminal session:

```bash
export BITRIX24_WEBHOOK_URL='https://haravan.bitrix24.vn/rest/USER_ID/WEBHOOK_SECRET'
```

Do not include a trailing slash if you use the test commands below.

Verify the variable is present without printing the secret:

```bash
test -n "$BITRIX24_WEBHOOK_URL" && echo "BITRIX24_WEBHOOK_URL is set"
```

## 5. Test real portal REST calls

### Test current user

```bash
curl -sS "$BITRIX24_WEBHOOK_URL/user.current.json"
```

Expected result: JSON response with a `result` object for the webhook owner.

### Test CRM company fields

```bash
curl -sS \
  -H "Content-Type: application/json" \
  -d '{}' \
  "$BITRIX24_WEBHOOK_URL/crm.company.userfield.list.json"
```

Expected result: JSON response with `result` as a list of custom fields.

### Test one company by ID

Replace `10` with a real Bitrix24 company ID.

```bash
curl -sS \
  -H "Content-Type: application/json" \
  -d '{"ID": 10}' \
  "$BITRIX24_WEBHOOK_URL/crm.company.get.json"
```

Expected result: JSON response with `result.ID`, `result.TITLE`, and any available `UF_CRM_*` fields.

### Test lead list

```bash
curl -sS \
  -H "Content-Type: application/json" \
  -d '{"select":["ID","TITLE","DATE_CREATE"],"order":{"ID":"DESC"}}' \
  "$BITRIX24_WEBHOOK_URL/crm.lead.list.json"
```

Expected result: JSON response with recent CRM leads.

## 6. Troubleshooting

If Bitrix24 returns `ACCESS_DENIED`, edit the inbound webhook and add the missing scope, usually `crm`.

If Bitrix24 returns `ERROR_METHOD_NOT_FOUND`, check the method name and confirm the webhook has permission for that module.

If Codex can list `b24-dev-mcp` but cannot use Bitrix24 tools, restart or reconnect the Codex session so it reloads MCP tools.

If a terminal command returns HTML instead of JSON, verify that the webhook URL is complete and has this shape:

```text
https://haravan.bitrix24.vn/rest/USER_ID/WEBHOOK_SECRET
```
