# AI Providers (/docs/automation/ai-providers)



Use Scopture from an assistant that supports remote MCP servers and OAuth sign-in. The server address is the same for every provider:

```text
https://api.scopture.com/mcp
```

Name the connection **Scopture**, choose **Streamable HTTP** when a transport is requested, and complete the Scopture sign-in. The connection uses your drawing permissions. Availability, menu names, and administrator requirements depend on the provider and your account.

## ChatGPT [#chatgpt]

1. Open ChatGPT’s **Plugins** page and choose **Add custom MCP server**.
2. Enter the Scopture server URL and select OAuth authentication.
3. Sign in to Scopture, finish creating the connection, and enable it in a chat.

Reference: [OpenAI - Add a custom MCP server](https://developers.openai.com/api/docs/guides/custom-mcp-server).

## Claude [#claude]

1. Open **Customize → Connectors** and add a custom web connector.
2. Enter **Scopture** and the server URL. Keep OAuth enabled and choose automatic client registration when offered.
3. Sign in to Scopture and enable the connector for your conversation.

Reference: [Claude - Add a custom connector](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp).

## Gemini [#gemini]

1. Open [Gemini](https://gemini.google.com) → **Settings → Connected Apps**.
2. Under **Custom apps**, choose **Add a custom app** and enter the server URL.
3. Choose **Next** and sign in to Scopture. Type `@` in a chat to select the app.

Reference: [Google - Connect custom apps to Gemini](https://support.google.com/gemini/answer/17209137). Availability depends on your account and region.

## Microsoft Copilot [#microsoft-copilot]

For **Microsoft 365 Copilot**:

1. Ask your Microsoft 365 admin to register Scopture as a custom federated connector using `https://api.scopture.com/mcp` as the MCP endpoint.
2. Have the admin configure the required authentication and make the connector available to your account.
3. In Copilot, open **Connectors** and enable Scopture.

Reference: [Microsoft - Set up custom federated connectors](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/set-up-custom-federated-connectors), [Microsoft - Connect Copilot to other services](https://support.microsoft.com/en-us/microsoft-copilot/connecting-microsoft-copilot-to-other-services).

For an agent built in **Copilot Studio**:

1. Open the agent’s **Build → Tools → Add tool → Model Context Protocol (MCP)**.
2. Add a custom server by URL and enter `https://api.scopture.com/mcp` with the authentication required by Scopture.
3. Add the server’s tools to the agent and save.

Reference: [Microsoft - Add an MCP server in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/tools-add-mcp-server).

## Grok [#grok]

1. Open [Grok Connectors](https://grok.com/connectors).
2. Choose **New Connector → Custom**, then enter the Scopture server URL.
3. Complete the Scopture sign-in and use the connector in your conversation.

Reference: [Grok - Connectors](https://docs.x.ai/grok/connectors).

## Perplexity [#perplexity]

1. Open Perplexity’s connector settings and add a **custom remote connector**.
2. Name it **Scopture**, paste the server URL, and select OAuth authentication.
3. Sign in to Scopture and enable the connector for your conversation or Computer workflow.

Reference: [Perplexity - Bring Your Own Connector](https://www.perplexity.ai/help-center/en/articles/11502712-local-and-remote-mcps-for-perplexity).

## Check the Connection [#check-the-connection]

Ask your assistant to “List my available drawings in Scopture,” then inspect the returned tool result. To work in a named drawing, ask it to resolve that drawing first rather than assuming the active canvas is the target.

Remote MCP works with cloud drawings. For local `.duc` files, use the [CLI Tool](/docs/automation/cli-tool) from an assistant with terminal access. See [MCP Tool](/docs/automation/mcp-tool) for capabilities and permissions, [SQLite Runner](/docs/automation/sqlite-runner) for structured queries, and [Python Sandbox](/docs/automation/python-sandbox) for computations and drawing updates.