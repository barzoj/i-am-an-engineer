/**
 * i-am-an-engineer: OpenCode 2 plugin.
 * Passthrough `iae_run` tool + fal MCP when FAL_KEY is set.
 */
import { spawn } from "node:child_process"
import { accessSync, constants } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { homedir } from "node:os"

import { Plugin } from "@opencode/plugin"

const PLUGIN_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..")

const GROUPS = [
  "init", "doctor", "record", "script", "ingest", "transcribe", "twin", "voice",
  "generate", "broll", "compose", "export", "run", "publish", "kb", "backend",
  "heygen", "elevenlabs", "fal", "deepinfra",
]

function falMcp(key: string) {
  return {
    type: "remote" as const,
    url: "https://mcp.fal.ai/mcp",
    headers: { Authorization: `Bearer ${key}` },
    oauth: false as const,
    disabled: false,
  }
}

function expandPath(path: string, base: string): string {
  if (path === "~") return homedir()
  if (path.startsWith("~/") || path.startsWith("~\\")) return join(homedir(), path.slice(2))
  return resolve(base, path)
}

function resolveIae(root: string, override?: string): string {
  if (override) return override
  if (process.platform === "win32") return "iae"
  const local = join(root, "bin", "iae")
  try {
    accessSync(local, constants.X_OK)
    return local
  } catch {
    return "iae"
  }
}

function run(command: string, args: string[], cwd: string, signal: AbortSignal) {
  return new Promise<{ code: number; out: string; err: string }>((done) => {
    const child = spawn(command, args, { cwd, signal, env: process.env })
    let out = ""
    let err = ""
    child.stdout?.setEncoding("utf8")
    child.stderr?.setEncoding("utf8")
    child.stdout?.on("data", (chunk) => (out += chunk))
    child.stderr?.on("data", (chunk) => (err += chunk))
    child.on("error", (error) => done({ code: -1, out, err: `${err}${String(error)}` }))
    child.on("close", (code) => done({ code: code ?? -1, out, err }))
  })
}

export default Plugin.define({
  id: "i-am-an-engineer",
  async setup(ctx) {
    const project = ctx.location.directory
    const root = typeof ctx.options.root === "string" ? expandPath(ctx.options.root, project) : PLUGIN_ROOT
    const iae = resolveIae(root, typeof ctx.options.command === "string" ? ctx.options.command : undefined)

    await ctx.mcp.transform((editor) => {
      const key = process.env.FAL_KEY
      if (key && !editor.get("fal")) editor.set("fal", falMcp(key))
    })

    await ctx.tool.transform((editor) => {
      editor.namespace({
        name: "iae",
        description: `i-am-an-engineer toolkit (${iae}). Record once → digital twin ads.`,
      })
      editor.add({
        name: "run",
        description:
          "Run the i-am-an-engineer `iae` CLI. `args` is the command line after `iae`. Groups: " +
          GROUPS.join(", ") + ".",
        input: {
          type: "object",
          properties: {
            args: { type: "array", items: { type: "string" }, description: "Arguments for `iae`." },
            cwd: { type: "string", description: "Working directory." },
          },
          required: ["args"],
          additionalProperties: false,
        },
        options: { namespace: "iae", codemode: true },
        execute: async (input, context) => {
          const parsed = (input ?? {}) as { args?: string[]; cwd?: string }
          const args = parsed.args ?? []
          const cwd = parsed.cwd ? expandPath(parsed.cwd, project) : project
          const result = await run(iae, args, cwd, context.signal)
          const body = [result.out.trimEnd(), result.err.trimEnd()].filter(Boolean).join("\n")
          return {
            content: `iae ${args.join(" ")}${result.code === 0 ? "" : ` (exit ${result.code})`}\n\n${body || "(no output)"}`,
          }
        },
      })
    })
  },
})
