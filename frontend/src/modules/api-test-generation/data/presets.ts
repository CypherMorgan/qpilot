/** OpenAPI spec presets — real-world API examples for test generation. */

export interface ApiTestPreset {
  id: string;
  title: string;
  description: string;
  specFormat: "yaml" | "json";
  content: string;
}

export const API_TEST_PRESETS: ApiTestPreset[] = [
  {
    id: "payment-intents",
    title: "Payment Intents API",
    description: "Stripe-style payment processing with webhooks",
    specFormat: "json",
    content: JSON.stringify(
      {
        openapi: "3.1.0",
        info: {
          title: "Payment Intents API",
          version: "1.0.0",
          description:
            "Payment processing API supporting one-time payments, recurring subscriptions, refunds, and dispute management. Integrates with Stripe Connect for marketplace payouts.",
        },
        servers: [{ url: "https://api.example.com/v1" }],
        paths: {
          "/payment_intents": {
            post: {
              operationId: "createPaymentIntent",
              summary: "Create a payment intent",
              description:
                "Creates a PaymentIntent object. After creation, the client confirms the payment on the frontend using the returned client_secret.",
              security: [{ apiKey: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["amount", "currency"],
                      properties: {
                        amount: {
                          type: "integer",
                          description: "Amount in cents",
                          example: 2000,
                          minimum: 50,
                          maximum: 99999999,
                        },
                        currency: {
                          type: "string",
                          description: "Three-letter ISO currency code",
                          example: "usd",
                          pattern: "^[a-z]{3}$",
                        },
                        capture_method: {
                          type: "string",
                          enum: ["automatic", "manual"],
                          default: "automatic",
                        },
                        confirm: { type: "boolean", default: false },
                        payment_method: { type: "string", nullable: true },
                        description: { type: "string", maxLength: 500 },
                        metadata: {
                          type: "object",
                          additionalProperties: { type: "string" },
                          maxProperties: 20,
                        },
                        customer_id: {
                          type: "string",
                          pattern: "^cus_[a-zA-Z0-9]+$",
                        },
                        statement_descriptor: {
                          type: "string",
                          maxLength: 22,
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": {
                  description: "PaymentIntent created",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        required: [
                          "id",
                          "amount",
                          "currency",
                          "status",
                          "client_secret",
                        ],
                        properties: {
                          id: {
                            type: "string",
                            pattern: "^pi_[a-zA-Z0-9]+$",
                          },
                          amount: { type: "integer" },
                          currency: { type: "string" },
                          status: {
                            type: "string",
                            enum: [
                              "requires_payment_method",
                              "requires_confirmation",
                              "requires_action",
                              "processing",
                              "succeeded",
                              "canceled",
                            ],
                          },
                          client_secret: { type: "string" },
                          created: {
                            type: "integer",
                            description: "Unix timestamp",
                          },
                        },
                      },
                    },
                  },
                },
                "400": {
                  $ref: "#/components/responses/ValidationError",
                },
                "402": {
                  $ref: "#/components/responses/PaymentError",
                },
              },
            },
            get: {
              operationId: "listPaymentIntents",
              summary: "List all payment intents",
              parameters: [
                {
                  name: "customer",
                  in: "query",
                  schema: { type: "string", pattern: "^cus_" },
                },
                {
                  name: "status",
                  in: "query",
                  schema: {
                    type: "string",
                    enum: [
                      "requires_payment_method",
                      "requires_confirmation",
                      "processing",
                      "succeeded",
                      "canceled",
                    ],
                  },
                },
                {
                  name: "limit",
                  in: "query",
                  schema: { type: "integer", minimum: 1, maximum: 100, default: 10 },
                },
                {
                  name: "starting_after",
                  in: "query",
                  schema: { type: "string" },
                },
              ],
              responses: {
                "200": {
                  description: "Paginated list of payment intents",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          data: {
                            type: "array",
                            items: { $ref: "#/components/schemas/PaymentIntent" },
                          },
                          has_more: { type: "boolean" },
                          total_count: { type: "integer" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/payment_intents/{id}/confirm": {
            post: {
              operationId: "confirmPaymentIntent",
              summary: "Confirm a payment intent",
              parameters: [
                {
                  name: "id",
                  in: "path",
                  required: true,
                  schema: { type: "string", pattern: "^pi_" },
                },
              ],
              requestBody: {
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      properties: {
                        payment_method: { type: "string" },
                        return_url: { type: "string", format: "uri" },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  $ref: "#/components/responses/PaymentIntentSuccess",
                },
              },
            },
          },
          "/payment_intents/{id}/cancel": {
            post: {
              operationId: "cancelPaymentIntent",
              summary: "Cancel a payment intent",
              parameters: [
                {
                  name: "id",
                  in: "path",
                  required: true,
                  schema: { type: "string", pattern: "^pi_" },
                },
              ],
              responses: {
                "200": {
                  $ref: "#/components/responses/PaymentIntentSuccess",
                },
              },
            },
          },
          "/refunds": {
            post: {
              operationId: "createRefund",
              summary: "Create a refund",
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["payment_intent"],
                      properties: {
                        payment_intent: {
                          type: "string",
                          pattern: "^pi_",
                        },
                        amount: {
                          type: "integer",
                          description: "Amount to refund in cents. Defaults to full amount.",
                        },
                        reason: {
                          type: "string",
                          enum: [
                            "requested_by_customer",
                            "duplicate",
                            "fraudulent",
                          ],
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": {
                  description: "Refund created",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          id: { type: "string", pattern: "^re_" },
                          object: { type: "string", enum: ["refund"] },
                          amount: { type: "integer" },
                          status: {
                            type: "string",
                            enum: ["pending", "succeeded", "failed"],
                          },
                          payment_intent: { type: "string" },
                          failure_reason: { type: "string", nullable: true },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/webhooks": {
            post: {
              operationId: "handleWebhook",
              summary: "Handle Stripe webhook event",
              security: [{ webhookSignature: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["type", "data"],
                      properties: {
                        id: { type: "string" },
                        type: {
                          type: "string",
                          enum: [
                            "payment_intent.succeeded",
                            "payment_intent.payment_failed",
                            "charge.refunded",
                            "charge.dispute.created",
                            "charge.dispute.resolved",
                            "customer.subscription.updated",
                          ],
                        },
                        data: {
                          type: "object",
                          properties: {
                            object: { type: "object" },
                          },
                        },
                        created: { type: "integer" },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  description: "Webhook received",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          received: { type: "boolean", enum: [true] },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        components: {
          securitySchemes: {
            apiKey: {
              type: "http",
              scheme: "bearer",
              description:
                "Secret API key (sk_live_ or sk_test_ prefix)",
            },
            webhookSignature: {
              type: "http",
              scheme: "bearer",
              description: "Webhook signing secret (whsec_ prefix)",
            },
          },
          schemas: {
            PaymentIntent: {
              type: "object",
              properties: {
                id: { type: "string" },
                amount: { type: "integer" },
                currency: { type: "string" },
                status: { type: "string" },
                client_secret: { type: "string" },
                customer_id: { type: "string", nullable: true },
                payment_method: { type: "string", nullable: true },
                description: { type: "string", nullable: true },
                metadata: { type: "object" },
                created: { type: "integer" },
              },
            },
          },
          responses: {
            ValidationError: {
              description: "Validation error",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      error: {
                        type: "object",
                        properties: {
                          type: { type: "string", enum: ["validation_error"] },
                          message: { type: "string" },
                          code: { type: "string" },
                          param: { type: "string", nullable: true },
                        },
                      },
                    },
                  },
                },
              },
            },
            PaymentError: {
              description: "Payment error",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      error: {
                        type: "object",
                        properties: {
                          type: {
                            type: "string",
                            enum: [
                              "card_declined",
                              "insufficient_funds",
                              "lost_card",
                              "stolen_card",
                              "expired_card",
                              "processing_error",
                            ],
                          },
                          message: { type: "string" },
                          decline_code: { type: "string", nullable: true },
                        },
                      },
                    },
                  },
                },
              },
            },
            PaymentIntentSuccess: {
              description: "Payment intent response",
              content: {
                "application/json": {
                  schema: {
                    $ref: "#/components/schemas/PaymentIntent",
                  },
                },
              },
            },
          },
        },
      },
      null,
      2,
    ),
  },
  {
    id: "issues-api",
    title: "Issues & Repos API",
    description: "GitHub-style issue tracking and repository management",
    specFormat: "json",
    content: JSON.stringify(
      {
        openapi: "3.1.0",
        info: {
          title: "Repository Management API",
          version: "1.0.0",
          description:
            "Manage repositories, issues, pull requests, and code reviews. Supports GitHub/GitLab-style workflows with webhook notifications.",
        },
        servers: [{ url: "https://api.example.com/v1" }],
        paths: {
          "/repos": {
            get: {
              operationId: "listRepositories",
              summary: "List repositories",
              description: "List repositories accessible to the authenticated user.",
              security: [{ oauth2: ["repo:read"] }],
              parameters: [
                {
                  name: "type",
                  in: "query",
                  schema: {
                    type: "string",
                    enum: ["all", "owner", "member", "public"],
                    default: "all",
                  },
                },
                {
                  name: "sort",
                  in: "query",
                  schema: {
                    type: "string",
                    enum: ["created", "updated", "pushed", "full_name"],
                    default: "created",
                  },
                },
                { name: "direction", in: "query", schema: { type: "string", enum: ["asc", "desc"], default: "desc" } },
                { name: "per_page", in: "query", schema: { type: "integer", minimum: 1, maximum: 100, default: 30 } },
                { name: "page", in: "query", schema: { type: "integer", minimum: 1, default: 1 } },
              ],
              responses: {
                "200": {
                  description: "Repository list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "array",
                        items: { $ref: "#/components/schemas/Repository" },
                      },
                    },
                  },
                },
              },
            },
            post: {
              operationId: "createRepository",
              summary: "Create a repository",
              security: [{ oauth2: ["repo:write"] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["name"],
                      properties: {
                        name: { type: "string", pattern: "^[a-zA-Z0-9_.-]+$", minLength: 2, maxLength: 100 },
                        description: { type: "string", maxLength: 500 },
                        private: { type: "boolean", default: false },
                        auto_init: { type: "boolean", default: false },
                        gitignore_template: { type: "string" },
                        license_template: { type: "string" },
                        allow_squash_merge: { type: "boolean", default: true },
                        allow_merge_commit: { type: "boolean", default: true },
                        allow_rebase_merge: { type: "boolean", default: true },
                        delete_branch_on_merge: { type: "boolean", default: false },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": { $ref: "#/components/responses/RepositoryResponse" },
                "422": { description: "Repository creation failed" },
              },
            },
          },
          "/repos/{owner}/{repo}/issues": {
            get: {
              operationId: "listIssues",
              summary: "List repository issues",
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
                {
                  name: "state",
                  in: "query",
                  schema: { type: "string", enum: ["open", "closed", "all"], default: "open" },
                },
                { name: "labels", in: "query", schema: { type: "string", description: "Comma-separated label names" } },
                { name: "assignee", in: "query", schema: { type: "string", nullable: true } },
                { name: "milestone", in: "query", schema: { type: "string", nullable: true } },
                { name: "since", in: "query", schema: { type: "string", format: "date-time" } },
                { name: "sort", in: "query", schema: { type: "string", enum: ["created", "updated", "comments"], default: "created" } },
                { name: "per_page", in: "query", schema: { type: "integer", minimum: 1, maximum: 100, default: 30 } },
              ],
              responses: {
                "200": {
                  description: "Issue list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "array",
                        items: { $ref: "#/components/schemas/Issue" },
                      },
                    },
                  },
                },
              },
            },
            post: {
              operationId: "createIssue",
              summary: "Create an issue",
              security: [{ oauth2: ["issues:write"] }],
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
              ],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["title"],
                      properties: {
                        title: { type: "string", minLength: 1, maxLength: 500 },
                        body: { type: "string", maxLength: 65536 },
                        assignees: { type: "array", items: { type: "string" } },
                        labels: { type: "array", items: { type: "string" } },
                        milestone: { type: "integer" },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": { $ref: "#/components/responses/IssueResponse" },
                "422": { description: "Validation failed" },
              },
            },
          },
          "/repos/{owner}/{repo}/issues/{issue_number}/comments": {
            get: {
              operationId: "listIssueComments",
              summary: "List issue comments",
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
                { name: "issue_number", in: "path", required: true, schema: { type: "integer", minimum: 1 } },
                { name: "since", in: "query", schema: { type: "string", format: "date-time" } },
                { name: "per_page", in: "query", schema: { type: "integer", maximum: 100, default: 30 } },
              ],
              responses: {
                "200": {
                  description: "Comment list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "array",
                        items: { $ref: "#/components/schemas/IssueComment" },
                      },
                    },
                  },
                },
              },
            },
            post: {
              operationId: "createIssueComment",
              summary: "Create an issue comment",
              security: [{ oauth2: ["issues:write"] }],
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
                { name: "issue_number", in: "path", required: true, schema: { type: "integer" } },
              ],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["body"],
                      properties: {
                        body: { type: "string", maxLength: 65536 },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": { $ref: "#/components/responses/CommentResponse" },
              },
            },
          },
          "/repos/{owner}/{repo}/pulls": {
            get: {
              operationId: "listPullRequests",
              summary: "List pull requests",
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
                {
                  name: "state",
                  in: "query",
                  schema: { type: "string", enum: ["open", "closed", "merged", "all"], default: "open" },
                },
                { name: "head", in: "query", schema: { type: "string", description: "Filter by head branch" } },
                { name: "base", in: "query", schema: { type: "string", description: "Filter by base branch" } },
                { name: "sort", in: "query", schema: { type: "string", enum: ["created", "updated", "popularity", "long-running"] } },
              ],
              responses: {
                "200": {
                  description: "Pull request list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "array",
                        items: { $ref: "#/components/schemas/PullRequest" },
                      },
                    },
                  },
                },
              },
            },
            post: {
              operationId: "createPullRequest",
              summary: "Create a pull request",
              security: [{ oauth2: ["pulls:write"] }],
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
              ],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["title", "head", "base"],
                      properties: {
                        title: { type: "string" },
                        body: { type: "string" },
                        head: { type: "string", description: "The name of the branch where changes are implemented" },
                        base: { type: "string", description: "The name of the branch you want changes pulled into" },
                        draft: { type: "boolean", default: false },
                        maintainer_can_modify: { type: "boolean", default: true },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": { $ref: "#/components/responses/PullRequestResponse" },
              },
            },
          },
          "/repos/{owner}/{repo}/pulls/{pull_number}/merge": {
            put: {
              operationId: "mergePullRequest",
              summary: "Merge a pull request",
              security: [{ oauth2: ["pulls:write"] }],
              parameters: [
                { name: "owner", in: "path", required: true, schema: { type: "string" } },
                { name: "repo", in: "path", required: true, schema: { type: "string" } },
                { name: "pull_number", in: "path", required: true, schema: { type: "integer" } },
              ],
              requestBody: {
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      properties: {
                        commit_title: { type: "string" },
                        commit_message: { type: "string" },
                        merge_method: {
                          type: "string",
                          enum: ["merge", "squash", "rebase"],
                          default: "merge",
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  description: "Merge result",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          merged: { type: "boolean" },
                          message: { type: "string" },
                          sha: { type: "string" },
                        },
                      },
                    },
                  },
                },
                "409": { description: "Merge conflict" },
              },
            },
          },
        },
        components: {
          securitySchemes: {
            oauth2: {
              type: "oauth2",
              flows: {
                authorizationCode: {
                  authorizationUrl: "https://example.com/oauth/authorize",
                  tokenUrl: "https://example.com/oauth/token",
                  scopes: {
                    "repo:read": "Read repository metadata",
                    "repo:write": "Create and modify repositories",
                    "issues:write": "Create and edit issues",
                    "pulls:write": "Create and merge pull requests",
                  },
                },
              },
            },
          },
          schemas: {
            Repository: {
              type: "object",
              properties: {
                id: { type: "integer" },
                name: { type: "string" },
                full_name: { type: "string" },
                private: { type: "boolean" },
                description: { type: "string", nullable: true },
                fork: { type: "boolean" },
                html_url: { type: "string", format: "uri" },
                default_branch: { type: "string" },
                language: { type: "string", nullable: true },
                open_issues_count: { type: "integer" },
                stars_count: { type: "integer" },
                forks_count: { type: "integer" },
                created_at: { type: "string", format: "date-time" },
                updated_at: { type: "string", format: "date-time" },
                pushed_at: { type: "string", format: "date-time" },
              },
              required: ["id", "name", "full_name", "private", "html_url", "default_branch"],
            },
            Issue: {
              type: "object",
              properties: {
                id: { type: "integer" },
                number: { type: "integer" },
                title: { type: "string" },
                state: { type: "string", enum: ["open", "closed"] },
                locked: { type: "boolean" },
                body: { type: "string", nullable: true },
                labels: {
                  type: "array",
                  items: {
                    type: "object",
                    properties: {
                      id: { type: "integer" },
                      name: { type: "string" },
                      color: { type: "string" },
                    },
                  },
                },
                assignees: {
                  type: "array",
                  items: { $ref: "#/components/schemas/User" },
                },
                milestone: { type: "object", nullable: true },
                comments_count: { type: "integer" },
                created_at: { type: "string", format: "date-time" },
                updated_at: { type: "string", format: "date-time" },
                closed_at: { type: "string", format: "date-time", nullable: true },
              },
            },
            IssueComment: {
              type: "object",
              properties: {
                id: { type: "integer" },
                body: { type: "string" },
                user: { $ref: "#/components/schemas/User" },
                created_at: { type: "string", format: "date-time" },
                updated_at: { type: "string", format: "date-time" },
                author_association: {
                  type: "string",
                  enum: ["COLLABORATOR", "CONTRIBUTOR", "FIRST_TIMER", "MEMBER", "OWNER", "NONE"],
                },
              },
            },
            PullRequest: {
              type: "object",
              properties: {
                id: { type: "integer" },
                number: { type: "integer" },
                title: { type: "string" },
                state: { type: "string", enum: ["open", "closed", "merged"] },
                body: { type: "string", nullable: true },
                draft: { type: "boolean" },
                head: { type: "object", properties: { ref: { type: "string" }, sha: { type: "string" } } },
                base: { type: "object", properties: { ref: { type: "string" }, sha: { type: "string" } } },
                mergeable: { type: "boolean", nullable: true },
                mergeable_state: { type: "string", enum: ["draft", "clean", "unstable", "blocked", "unknown"] },
                merged: { type: "boolean" },
                merged_by: { $ref: "#/components/schemas/User", nullable: true },
                commits_count: { type: "integer" },
                changed_files: { type: "integer" },
                additions: { type: "integer" },
                deletions: { type: "integer" },
                created_at: { type: "string", format: "date-time" },
              },
            },
            User: {
              type: "object",
              properties: {
                id: { type: "integer" },
                login: { type: "string" },
                avatar_url: { type: "string", format: "uri" },
                type: { type: "string", enum: ["User", "Bot"] },
              },
            },
          },
          responses: {
            RepositoryResponse: {
              description: "Repository details",
              content: { "application/json": { schema: { $ref: "#/components/schemas/Repository" } } },
            },
            IssueResponse: {
              description: "Issue details",
              content: { "application/json": { schema: { $ref: "#/components/schemas/Issue" } } },
            },
            CommentResponse: {
              description: "Comment details",
              content: { "application/json": { schema: { $ref: "#/components/schemas/IssueComment" } } },
            },
            PullRequestResponse: {
              description: "Pull request details",
              content: { "application/json": { schema: { $ref: "#/components/schemas/PullRequest" } } },
            },
          },
        },
      },
      null,
      2,
    ),
  },
  {
    id: "email-api",
    title: "Transactional Email API",
    description: "SendGrid-style email sending with templates and analytics",
    specFormat: "json",
    content: JSON.stringify(
      {
        openapi: "3.1.0",
        info: {
          title: "Email Service API",
          version: "2.0.0",
          description:
            "Send transactional emails, manage templates, track opens/clicks/bounces, and retrieve delivery activity. Supports single sends, batch sends, and scheduled sends.",
        },
        servers: [{ url: "https://api.example.com/v2" }],
        paths: {
          "/mail/send": {
            post: {
              operationId: "sendEmail",
              summary: "Send an email",
              description:
                "Sends a transactional email immediately. Supports dynamic template rendering, attachments, and custom headers.",
              security: [{ apiKey: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["from", "subject"],
                      oneOf: [
                        { required: ["content"] },
                        { required: ["template_id"] },
                      ],
                      properties: {
                        personalizations: {
                          type: "array",
                          minItems: 1,
                          maxItems: 1000,
                          items: {
                            type: "object",
                            required: ["to"],
                            properties: {
                              to: {
                                type: "array",
                                minItems: 1,
                                maxItems: 100,
                                items: { $ref: "#/components/schemas/EmailAddress" },
                              },
                              cc: {
                                type: "array",
                                items: { $ref: "#/components/schemas/EmailAddress" },
                              },
                              bcc: {
                                type: "array",
                                items: { $ref: "#/components/schemas/EmailAddress" },
                              },
                              subject: { type: "string" },
                              headers: {
                                type: "object",
                                additionalProperties: { type: "string" },
                              },
                              substitutions: {
                                type: "object",
                                additionalProperties: { type: "string" },
                                description: "Template variable substitutions",
                              },
                              dynamic_template_data: {
                                type: "object",
                                description: "Data for Handlebars-style templates",
                              },
                              send_at: {
                                type: "integer",
                                description: "Unix timestamp for scheduled send",
                              },
                            },
                          },
                        },
                        from: { $ref: "#/components/schemas/EmailAddress" },
                        reply_to: { $ref: "#/components/schemas/EmailAddress" },
                        subject: { type: "string", maxLength: 998 },
                        content: {
                          type: "array",
                          items: {
                            type: "object",
                            required: ["type", "value"],
                            properties: {
                              type: {
                                type: "string",
                                enum: ["text/plain", "text/html"],
                              },
                              value: { type: "string" },
                            },
                          },
                        },
                        template_id: {
                          type: "string",
                          pattern: "^d-[a-f0-9]{32}$",
                        },
                        attachments: {
                          type: "array",
                          maxItems: 10,
                          items: {
                            type: "object",
                            required: ["content", "filename"],
                            properties: {
                              content: {
                                type: "string",
                                description: "Base64-encoded file content",
                              },
                              filename: { type: "string" },
                              type: { type: "string", default: "application/octet-stream" },
                              disposition: {
                                type: "string",
                                enum: ["inline", "attachment"],
                                default: "attachment",
                              },
                            },
                          },
                        },
                        categories: {
                          type: "array",
                          maxItems: 10,
                          items: { type: "string", maxLength: 255 },
                        },
                        custom_args: {
                          type: "object",
                          maxProperties: 10,
                          additionalProperties: { type: "string" },
                        },
                        send_at: {
                          type: "integer",
                          description: "Unix timestamp for scheduled delivery",
                        },
                        batch_id: {
                          type: "string",
                          description: "Assign to a batch for grouped analytics",
                        },
                        ip_pool_name: { type: "string" },
                        mail_settings: {
                          type: "object",
                          properties: {
                            bypass_list_management: { type: "boolean" },
                            bypass_spam_management: { type: "boolean" },
                            bypass_bounce_management: { type: "boolean" },
                            bypass_unsubscribe_management: { type: "boolean" },
                            sandbox_mode: { type: "boolean" },
                          },
                        },
                        tracking_settings: {
                          type: "object",
                          properties: {
                            click_tracking: {
                              type: "object",
                              properties: {
                                enable: { type: "boolean", default: true },
                                enable_text: { type: "boolean", default: false },
                              },
                            },
                            open_tracking: {
                              type: "object",
                              properties: {
                                enable: { type: "boolean", default: true },
                                substitution_tag: { type: "string", default: "%open-track%" },
                              },
                            },
                            google_analytics: {
                              type: "object",
                              properties: {
                                enable: { type: "boolean" },
                                utm_source: { type: "string" },
                                utm_medium: { type: "string" },
                                utm_campaign: { type: "string" },
                                utm_term: { type: "string" },
                                utm_content: { type: "string" },
                              },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "202": {
                  description: "Email accepted for delivery",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          message_id: {
                            type: "string",
                            pattern: "^[a-f0-9]{32}$",
                          },
                          batch_id: { type: "string", nullable: true },
                          status: { type: "string", enum: ["accepted", "queued", "scheduled"] },
                          estimated_delivery_seconds: { type: "integer" },
                        },
                      },
                    },
                  },
                },
                "400": { $ref: "#/components/responses/BadRequest" },
                "413": { description: "Request entity too large (max 30MB)" },
                "429": { $ref: "#/components/responses/RateLimited" },
              },
            },
          },
          "/templates": {
            get: {
              operationId: "listTemplates",
              summary: "List email templates",
              parameters: [
                { name: "page_size", in: "query", schema: { type: "integer", default: 50, maximum: 200 } },
                { name: "page_token", in: "query", schema: { type: "string" } },
              ],
              responses: {
                "200": {
                  description: "Paginated template list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          templates: {
                            type: "array",
                            items: {
                              type: "object",
                              properties: {
                                id: { type: "string" },
                                name: { type: "string" },
                                version: { type: "integer" },
                                active: { type: "boolean" },
                                updated_at: { type: "string", format: "date-time" },
                              },
                            },
                          },
                          next_page_token: { type: "string", nullable: true },
                        },
                      },
                    },
                  },
                },
              },
            },
            post: {
              operationId: "createTemplate",
              summary: "Create an email template",
              security: [{ apiKey: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["name"],
                      properties: {
                        name: { type: "string", maxLength: 100 },
                        generation: {
                          type: "string",
                          enum: ["legacy", "dynamic"],
                          default: "dynamic",
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": {
                  description: "Template created",
                  headers: {
                    Location: { schema: { type: "string" } },
                  },
                },
              },
            },
          },
          "/templates/{template_id}/versions": {
            post: {
              operationId: "createTemplateVersion",
              summary: "Create a template version",
              security: [{ apiKey: [] }],
              parameters: [
                { name: "template_id", in: "path", required: true, schema: { type: "string" } },
              ],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["subject", "content"],
                      properties: {
                        subject: { type: "string" },
                        content: { type: "string", description: "HTML content with Handlebars variables" },
                        active: { type: "boolean", default: false },
                        editor: {
                          type: "string",
                          enum: ["code", "design"],
                          default: "code",
                        },
                        test_data: {
                          type: "object",
                          description: "Sample data for preview rendering",
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": { description: "Version created" },
              },
            },
          },
          "/stats": {
            get: {
              operationId: "getEmailStats",
              summary: "Retrieve email statistics",
              security: [{ apiKey: [] }],
              parameters: [
                { name: "start_date", in: "query", required: true, schema: { type: "string", format: "date" } },
                { name: "end_date", in: "query", required: true, schema: { type: "string", format: "date" } },
                {
                  name: "aggregated_by",
                  in: "query",
                  schema: { type: "string", enum: ["day", "week", "month"], default: "day" },
                },
                { name: "categories", in: "query", schema: { type: "string", description: "Comma-separated" } },
              ],
              responses: {
                "200": {
                  description: "Statistics",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          date: { type: "string", format: "date" },
                          requests: { type: "integer" },
                          delivered: { type: "integer" },
                          opens: { type: "integer" },
                          unique_opens: { type: "integer" },
                          clicks: { type: "integer" },
                          unique_clicks: { type: "integer" },
                          bounces: { type: "integer" },
                          blocks: { type: "integer" },
                          spam_reports: { type: "integer" },
                          unsubscribes: { type: "integer" },
                          deferred: { type: "integer" },
                          open_rate: { type: "number", format: "float" },
                          click_rate: { type: "number", format: "float" },
                          bounce_rate: { type: "number", format: "float" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/activity": {
            get: {
              operationId: "getEmailActivity",
              summary: "Retrieve email activity log",
              security: [{ apiKey: [] }],
              parameters: [
                { name: "limit", in: "query", schema: { type: "integer", default: 50, maximum: 500 } },
                { name: "message_id", in: "query", schema: { type: "string" } },
                { name: "to_email", in: "query", schema: { type: "string", format: "email" } },
                { name: "event", in: "query", schema: { type: "string", enum: ["processed", "delivered", "open", "click", "bounce", "dropped", "spam_report", "unsubscribe"] } },
                { name: "start_date", in: "query", schema: { type: "string", format: "date-time" } },
              ],
              responses: {
                "200": {
                  description: "Activity events",
                  content: {
                    "application/json": {
                      schema: {
                        type: "array",
                        items: {
                          type: "object",
                          properties: {
                            message_id: { type: "string" },
                            to_email: { type: "string" },
                            event: { type: "string" },
                            timestamp: { type: "integer" },
                            category: { type: "string" },
                            reason: { type: "string", nullable: true },
                            response: { type: "string", nullable: true },
                            ip: { type: "string" },
                            user_agent: { type: "string", nullable: true },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        components: {
          securitySchemes: {
            apiKey: {
              type: "http",
              scheme: "bearer",
              description: "Email API key (SG. prefix)",
            },
          },
          schemas: {
            EmailAddress: {
              type: "object",
              required: ["email"],
              properties: {
                email: { type: "string", format: "email", maxLength: 320 },
                name: { type: "string", maxLength: 255 },
              },
            },
          },
          responses: {
            BadRequest: {
              description: "Validation error",
              content: {
                "application/json": {
                  schema: {
                    type: "object",
                    properties: {
                      errors: {
                        type: "array",
                        items: {
                          type: "object",
                          properties: {
                            field: { type: "string" },
                            message: { type: "string" },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
            RateLimited: {
              description: "Rate limit exceeded",
              headers: {
                "X-RateLimit-Reset": { schema: { type: "integer" } },
                "Retry-After": { schema: { type: "integer" } },
              },
            },
          },
        },
      },
      null,
      2,
    ),
  },
  {
    id: "user-management",
    title: "User Management API",
    description: "Auth, profiles, roles, and admin management",
    specFormat: "json",
    content: JSON.stringify(
      {
        openapi: "3.1.0",
        info: {
          title: "User Management API",
          version: "2.1.0",
          description:
            "Complete user lifecycle management: registration, authentication (JWT + refresh tokens), profile CRUD, role-based access control, admin operations, and audit logging.",
        },
        servers: [{ url: "https://api.example.com/v2" }],
        paths: {
          "/auth/register": {
            post: {
              operationId: "registerUser",
              summary: "Register a new user account",
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["email", "password", "name"],
                      properties: {
                        email: { type: "string", format: "email", maxLength: 320 },
                        password: {
                          type: "string",
                          minLength: 8,
                          maxLength: 128,
                          pattern: "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+\\-=\\[\\]{}|;:',.<>?/~`]).{8,}$",
                          description: "Must contain uppercase, lowercase, number, and special character",
                        },
                        name: { type: "string", minLength: 1, maxLength: 200 },
                        accept_terms: { type: "boolean", enum: [true] },
                        referral_code: { type: "string", maxLength: 20, nullable: true },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": {
                  description: "User registered",
                  content: {
                    "application/json": {
                      schema: {
                        $ref: "#/components/schemas/AuthResponse",
                      },
                    },
                  },
                },
                "409": {
                  description: "Email already registered",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          error: { type: "string", enum: ["email_exists"] },
                          message: { type: "string" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/auth/login": {
            post: {
              operationId: "login",
              summary: "Authenticate user",
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["email", "password"],
                      properties: {
                        email: { type: "string", format: "email" },
                        password: { type: "string" },
                        totp_code: {
                          type: "string",
                          pattern: "^[0-9]{6}$",
                          description: "Required if 2FA is enabled",
                        },
                        device_info: {
                          type: "object",
                          properties: {
                            user_agent: { type: "string" },
                            ip_address: { type: "string", format: "ipv4" },
                            device_id: { type: "string" },
                          },
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  $ref: "#/components/responses/AuthSuccess",
                },
                "401": {
                  description: "Invalid credentials or 2FA required",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          error: {
                            type: "string",
                            enum: ["invalid_credentials", "2fa_required", "account_locked", "email_not_verified"],
                          },
                          message: { type: "string" },
                          remaining_attempts: { type: "integer" },
                          lockout_seconds: { type: "integer" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/auth/refresh": {
            post: {
              operationId: "refreshToken",
              summary: "Refresh access token",
              security: [{ bearerAuth: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["refresh_token"],
                      properties: {
                        refresh_token: { type: "string" },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": { $ref: "#/components/responses/AuthSuccess" },
                "401": { description: "Invalid or expired refresh token" },
              },
            },
          },
          "/auth/logout": {
            post: {
              operationId: "logout",
              summary: "Invalidate current session",
              security: [{ bearerAuth: [] }],
              requestBody: {
                content: {
                  "application/json": {
                    schema: {
                      properties: {
                        refresh_token: { type: "string" },
                        all_sessions: {
                          type: "boolean",
                          description: "Logout from all devices",
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "204": { description: "Logged out successfully" },
              },
            },
          },
          "/auth/password-reset": {
            post: {
              operationId: "requestPasswordReset",
              summary: "Request password reset email",
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["email"],
                      properties: {
                        email: { type: "string", format: "email" },
                      },
                    },
                  },
                },
              },
              responses: {
                "202": {
                  description: "Reset email sent (always returns 202 to prevent email enumeration)",
                },
              },
            },
          },
          "/auth/password-reset/confirm": {
            post: {
              operationId: "confirmPasswordReset",
              summary: "Complete password reset with token",
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["token", "new_password"],
                      properties: {
                        token: { type: "string" },
                        new_password: { type: "string", minLength: 8 },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": { $ref: "#/components/responses/AuthSuccess" },
                "400": { description: "Invalid or expired reset token" },
              },
            },
          },
          "/users/me": {
            get: {
              operationId: "getCurrentUser",
              summary: "Get current user profile",
              security: [{ bearerAuth: [] }],
              responses: {
                "200": {
                  description: "User profile",
                  content: {
                    "application/json": {
                      schema: { $ref: "#/components/schemas/UserProfile" },
                    },
                  },
                },
              },
            },
            patch: {
              operationId: "updateCurrentUser",
              summary: "Update current user profile",
              security: [{ bearerAuth: [] }],
              requestBody: {
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      properties: {
                        name: { type: "string", maxLength: 200 },
                        avatar_url: { type: "string", format: "uri", nullable: true },
                        bio: { type: "string", maxLength: 2000 },
                        phone: { type: "string", pattern: "^\\+[1-9]\\d{1,14}$", nullable: true },
                        preferred_language: { type: "string", pattern: "^[a-z]{2}(-[A-Z]{2})?$" },
                        notification_preferences: {
                          type: "object",
                          properties: {
                            email_notifications: { type: "boolean" },
                            push_notifications: { type: "boolean" },
                            weekly_digest: { type: "boolean" },
                            marketing_emails: { type: "boolean" },
                          },
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  description: "Updated profile",
                  content: {
                    "application/json": {
                      schema: { $ref: "#/components/schemas/UserProfile" },
                    },
                  },
                },
              },
            },
          },
          "/users/me/sessions": {
            get: {
              operationId: "listActiveSessions",
              summary: "List active sessions",
              security: [{ bearerAuth: [] }],
              responses: {
                "200": {
                  description: "Active sessions",
                  content: {
                    "application/json": {
                      schema: {
                        type: "array",
                        items: {
                          type: "object",
                          properties: {
                            session_id: { type: "string" },
                            device: { type: "string" },
                            ip_address: { type: "string" },
                            created_at: { type: "string", format: "date-time" },
                            last_active: { type: "string", format: "date-time" },
                            current: { type: "boolean" },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/admin/users": {
            get: {
              operationId: "adminListUsers",
              summary: "List all users (admin)",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "page", in: "query", schema: { type: "integer", default: 1, minimum: 1 } },
                { name: "per_page", in: "query", schema: { type: "integer", default: 30, maximum: 100 } },
                { name: "role", in: "query", schema: { type: "string", enum: ["user", "moderator", "admin"] } },
                { name: "status", in: "query", schema: { type: "string", enum: ["active", "suspended", "deleted"] } },
                { name: "search", in: "query", schema: { type: "string", minLength: 3 } },
                { name: "sort_by", in: "query", schema: { type: "string", enum: ["created_at", "email", "name", "last_login"] } },
              ],
              responses: {
                "200": {
                  description: "Paginated user list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          data: {
                            type: "array",
                            items: { $ref: "#/components/schemas/AdminUser" },
                          },
                          total: { type: "integer" },
                          page: { type: "integer" },
                          total_pages: { type: "integer" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/admin/users/{user_id}/suspend": {
            post: {
              operationId: "suspendUser",
              summary: "Suspend a user account (admin)",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "user_id", in: "path", required: true, schema: { type: "string" } },
              ],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["reason"],
                      properties: {
                        reason: { type: "string", maxLength: 1000 },
                        duration_hours: { type: "integer", nullable: true, description: "Null = permanent" },
                        notify_user: { type: "boolean", default: true },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  description: "User suspended",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          status: { type: "string", enum: ["suspended"] },
                          suspended_until: { type: "string", format: "date-time", nullable: true },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        components: {
          securitySchemes: {
            bearerAuth: {
              type: "http",
              scheme: "bearer",
              bearerFormat: "JWT",
              description: "Access token from login or refresh endpoint",
            },
          },
          schemas: {
            AuthResponse: {
              type: "object",
              properties: {
                access_token: { type: "string" },
                refresh_token: { type: "string" },
                expires_in: { type: "integer" },
                token_type: { type: "string", enum: ["Bearer"] },
                user: { $ref: "#/components/schemas/UserProfile" },
              },
            },
            UserProfile: {
              type: "object",
              properties: {
                id: { type: "string" },
                email: { type: "string", format: "email" },
                name: { type: "string" },
                avatar_url: { type: "string", format: "uri", nullable: true },
                role: { type: "string", enum: ["user", "moderator", "admin"] },
                email_verified: { type: "boolean" },
                two_factor_enabled: { type: "boolean" },
                created_at: { type: "string", format: "date-time" },
                last_login: { type: "string", format: "date-time" },
                notification_preferences: {
                  type: "object",
                  properties: {
                    email_notifications: { type: "boolean" },
                    push_notifications: { type: "boolean" },
                    weekly_digest: { type: "boolean" },
                  },
                },
              },
              required: ["id", "email", "name", "role"],
            },
            AdminUser: {
              allOf: [
                { $ref: "#/components/schemas/UserProfile" },
                {
                  type: "object",
                  properties: {
                    status: { type: "string", enum: ["active", "suspended", "deleted"] },
                    login_count: { type: "integer" },
                    suspended_at: { type: "string", format: "date-time", nullable: true },
                    suspension_reason: { type: "string", nullable: true },
                    metadata: { type: "object" },
                  },
                },
              ],
            },
          },
          responses: {
            AuthSuccess: {
              description: "Authentication successful",
              content: {
                "application/json": {
                  schema: { $ref: "#/components/schemas/AuthResponse" },
                },
              },
            },
          },
        },
      },
      null,
      2,
    ),
  },
  {
    id: "file-storage",
    title: "File Storage API",
    description: "S3-compatible object storage with folders and access control",
    specFormat: "json",
    content: JSON.stringify(
      {
        openapi: "3.1.0",
        info: {
          title: "Object Storage API",
          version: "1.0.0",
          description:
            "S3-compatible object storage service. Manage buckets, upload/download objects, set access policies, and generate presigned URLs for temporary access.",
        },
        servers: [{ url: "https://storage.example.com/v1" }],
        paths: {
          "/buckets": {
            get: {
              operationId: "listBuckets",
              summary: "List all buckets",
              security: [{ bearerAuth: [] }],
              responses: {
                "200": {
                  description: "Bucket list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          buckets: {
                            type: "array",
                            items: {
                              type: "object",
                              properties: {
                                id: { type: "string" },
                                name: {
                                  type: "string",
                                  pattern: "^[a-z0-9][a-z0-9.-]{2,62}[a-z0-9]$",
                                },
                                owner: { type: "string" },
                                region: { type: "string" },
                                created_at: { type: "string", format: "date-time" },
                                total_size_bytes: { type: "integer" },
                                object_count: { type: "integer" },
                                public: { type: "boolean" },
                                versioning_enabled: { type: "boolean" },
                              },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
            post: {
              operationId: "createBucket",
              summary: "Create a new bucket",
              security: [{ bearerAuth: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["name"],
                      properties: {
                        name: {
                          type: "string",
                          pattern: "^[a-z0-9][a-z0-9.-]{2,62}[a-z0-9]$",
                          description: "Globally unique bucket name (lowercase letters, numbers, dots, hyphens)",
                        },
                        region: {
                          type: "string",
                          default: "us-east-1",
                          enum: ["us-east-1", "eu-west-1", "ap-southeast-1"],
                        },
                        public: { type: "boolean", default: false },
                        versioning: { type: "boolean", default: false },
                        object_lock: {
                          type: "object",
                          properties: {
                            enabled: { type: "boolean", default: false },
                            retention_mode: {
                              type: "string",
                              enum: ["governance", "compliance"],
                            },
                            retention_days: {
                              type: "integer",
                              minimum: 1,
                              maximum: 36500,
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "201": { description: "Bucket created" },
                "409": { description: "Bucket name already taken" },
              },
            },
          },
          "/buckets/{bucket}/objects": {
            get: {
              operationId: "listObjects",
              summary: "List objects in a bucket",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "prefix", in: "query", schema: { type: "string" } },
                { name: "delimiter", in: "query", schema: { type: "string", default: "/" } },
                { name: "max_keys", in: "query", schema: { type: "integer", maximum: 1000, default: 100 } },
                { name: "marker", in: "query", schema: { type: "string" } },
                { name: "include_versions", in: "query", schema: { type: "boolean", default: false } },
              ],
              responses: {
                "200": {
                  description: "Object list",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          objects: {
                            type: "array",
                            items: { $ref: "#/components/schemas/ObjectMeta" },
                          },
                          prefixes: {
                            type: "array",
                            items: { type: "string" },
                            description: "Common prefixes when using delimiter",
                          },
                          is_truncated: { type: "boolean" },
                          next_marker: { type: "string", nullable: true },
                          object_count: { type: "integer" },
                          total_size_bytes: { type: "integer" },
                        },
                      },
                    },
                  },
                },
              },
            },
            put: {
              operationId: "uploadObject",
              summary: "Upload an object",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "key", in: "query", required: true, schema: { type: "string", description: "Object key (path)" } },
              ],
              requestBody: {
                required: true,
                content: {
                  "application/octet-stream": {
                    schema: { type: "string", format: "binary" },
                  },
                },
              },
              responses: {
                "201": {
                  description: "Object uploaded",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          key: { type: "string" },
                          version_id: { type: "string", nullable: true },
                          etag: { type: "string" },
                          size_bytes: { type: "integer" },
                          storage_class: {
                            type: "string",
                            enum: ["STANDARD", "STANDARD_IA", "GLACIER", "DEEP_ARCHIVE"],
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/buckets/{bucket}/objects/{key}": {
            get: {
              operationId: "getObject",
              summary: "Download an object",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "key", in: "path", required: true, schema: { type: "string" } },
                { name: "version_id", in: "query", schema: { type: "string" } },
                { name: "range", in: "header", schema: { type: "string", description: "HTTP Range header for partial downloads" } },
              ],
              responses: {
                "200": {
                  description: "Object data",
                  content: {
                    "application/octet-stream": {
                      schema: { type: "string", format: "binary" },
                    },
                  },
                  headers: {
                    "Content-Type": { schema: { type: "string" } },
                    "Content-Length": { schema: { type: "integer" } },
                    "ETag": { schema: { type: "string" } },
                    "x-amz-version-id": { schema: { type: "string" } },
                    "x-amz-storage-class": { schema: { type: "string" } },
                    "Accept-Ranges": { schema: { type: "string", enum: ["bytes"] } },
                  },
                },
                "206": {
                  description: "Partial content (Range request)",
                  headers: {
                    "Content-Range": { schema: { type: "string" } },
                  },
                },
                "404": { description: "Object not found" },
              },
            },
            delete: {
              operationId: "deleteObject",
              summary: "Delete an object",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "key", in: "path", required: true, schema: { type: "string" } },
                { name: "version_id", in: "query", schema: { type: "string" } },
                { name: "bypass_governance_retention", in: "header", schema: { type: "boolean" } },
              ],
              responses: {
                "204": {
                  description: "Object deleted",
                  headers: {
                    "x-amz-delete-marker": { schema: { type: "boolean" } },
                    "x-amz-version-id": { schema: { type: "string" } },
                  },
                },
              },
            },
          },
          "/buckets/{bucket}/uploads": {
            post: {
              operationId: "initiateMultipartUpload",
              summary: "Start a multipart upload",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "key", in: "query", required: true, schema: { type: "string" } },
              ],
              responses: {
                "200": {
                  description: "Upload ID",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          upload_id: { type: "string" },
                          key: { type: "string" },
                          bucket: { type: "string" },
                          initiated_at: { type: "string", format: "date-time" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/buckets/{bucket}/uploads/{upload_id}": {
            put: {
              operationId: "uploadPart",
              summary: "Upload a part",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "upload_id", in: "path", required: true, schema: { type: "string" } },
                { name: "part_number", in: "query", required: true, schema: { type: "integer", minimum: 1, maximum: 10000 } },
              ],
              responses: {
                "200": {
                  description: "Part uploaded",
                  headers: {
                    "ETag": { schema: { type: "string" } },
                  },
                },
              },
            },
            post: {
              operationId: "completeMultipartUpload",
              summary: "Complete a multipart upload",
              security: [{ bearerAuth: [] }],
              parameters: [
                { name: "bucket", in: "path", required: true, schema: { type: "string" } },
                { name: "upload_id", in: "path", required: true, schema: { type: "string" } },
              ],
              requestBody: {
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["parts"],
                      properties: {
                        parts: {
                          type: "array",
                          items: {
                            type: "object",
                            required: ["part_number", "etag"],
                            properties: {
                              part_number: { type: "integer" },
                              etag: { type: "string" },
                            },
                          },
                        },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  description: "Multipart upload complete",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          key: { type: "string" },
                          version_id: { type: "string" },
                          etag: { type: "string" },
                          size_bytes: { type: "integer" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "/presigned-url": {
            post: {
              operationId: "generatePresignedUrl",
              summary: "Generate a presigned URL",
              security: [{ bearerAuth: [] }],
              requestBody: {
                required: true,
                content: {
                  "application/json": {
                    schema: {
                      type: "object",
                      required: ["bucket", "key", "method"],
                      properties: {
                        bucket: { type: "string" },
                        key: { type: "string" },
                        method: {
                          type: "string",
                          enum: ["GET", "PUT", "DELETE"],
                        },
                        expires_in_seconds: {
                          type: "integer",
                          minimum: 60,
                          maximum: 86400,
                          default: 3600,
                        },
                        content_type: { type: "string" },
                      },
                    },
                  },
                },
              },
              responses: {
                "200": {
                  description: "Presigned URL",
                  content: {
                    "application/json": {
                      schema: {
                        type: "object",
                        properties: {
                          url: { type: "string", format: "uri" },
                          expires_at: { type: "string", format: "date-time" },
                          method: { type: "string" },
                          headers: {
                            type: "object",
                            additionalProperties: { type: "string" },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        components: {
          securitySchemes: {
            bearerAuth: {
              type: "http",
              scheme: "bearer",
              description: "Storage access token",
            },
          },
          schemas: {
            ObjectMeta: {
              type: "object",
              properties: {
                key: { type: "string" },
                size_bytes: { type: "integer" },
                etag: { type: "string" },
                storage_class: { type: "string" },
                content_type: { type: "string" },
                version_id: { type: "string", nullable: true },
                is_latest: { type: "boolean" },
                owner: { type: "string" },
                last_modified: {
                  type: "string",
                  format: "date-time",
                },
              },
            },
          },
        },
      },
      null,
      2,
    ),
  },
];
