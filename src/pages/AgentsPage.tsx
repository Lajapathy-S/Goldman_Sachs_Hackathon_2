import { useEffect, useRef, useState } from 'react'
import {
  SCENARIO_PRESETS,
  genericFinancialResponse,
  isFinancialQuery,
  matchScenario,
  type TransparentPlan,
} from './agentResponses'
import './AgentsPage.css'

type ChatRole = 'user' | 'assistant'

type ChatMessage = {
  id: string
  role: ChatRole
  text?: string
  plan?: TransparentPlan
  guardrail?: boolean
}

function PlanCard({ plan }: { plan: TransparentPlan }) {
  return (
    <div className="agent-plan">
      <p className="agent-plan-headline">{plan.headline}</p>
      <div className="agent-plan-section">
        <h3 className="agent-plan-h">Rebalancing strategy (easy steps)</h3>
        <ol className="agent-plan-list">
          {plan.strategy.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </div>
      <div className="agent-transparency">
        <div className="agent-t-block">
          <h4>Why this recommendation</h4>
          <p>{plan.why}</p>
        </div>
        <div className="agent-t-block">
          <h4>Costs to expect</h4>
          <p>{plan.costs}</p>
        </div>
        <div className="agent-t-block">
          <h4>Tax implications</h4>
          <p>{plan.tax}</p>
        </div>
        <div className="agent-t-block">
          <h4>Fit with your long-term goals</h4>
          <p>{plan.goals}</p>
        </div>
      </div>
    </div>
  )
}

export function AgentsPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  function pushMessage(m: ChatMessage) {
    setMessages((prev) => [...prev, m])
  }

  function respondToFinancialText(text: string) {
    const plan = matchScenario(text) ?? genericFinancialResponse()
    pushMessage({
      id: crypto.randomUUID(),
      role: 'assistant',
      plan,
    })
  }

  function handleSend(raw?: string) {
    const text = (raw ?? input).trim()
    if (!text) return
    setInput('')
    pushMessage({ id: crypto.randomUUID(), role: 'user', text })

    if (!isFinancialQuery(text)) {
      pushMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        guardrail: true,
        text: 'I can only help with portfolio and financial questions — for example rebalancing, risk, inflation, withdrawals, mutual funds, or taxes at a high level. Try a “What if…” scenario below or ask how to rebalance after a market move.',
      })
      return
    }

    respondToFinancialText(text)
  }

  function onPreset(prompt: string) {
    pushMessage({ id: crypto.randomUUID(), role: 'user', text: prompt })
    respondToFinancialText(prompt)
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    handleSend()
  }

  return (
    <div className="agents-shell">
      <div className="agents-chat-wrap container">
        <header className="agents-chat-header">
          <span className="agents-spark" aria-hidden>
            ✦
          </span>
          <h1>Start with a prompt</h1>
          <p className="agents-chat-sub">
            Ask about your portfolio in plain language. This agent focuses on scenario-based
            rebalancing ideas and explains the reasoning in simple terms — it does not place trades.
          </p>
        </header>

        <div className="agents-prompt-hero" aria-label="Suggested scenarios">
          <p className="agents-prompt-label">What-if scenarios</p>
          <div className="agents-chips">
            {SCENARIO_PRESETS.map((s) => (
              <button key={s.id} type="button" className="agents-chip" onClick={() => onPreset(s.prompt)}>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        <div className="agents-messages" ref={listRef} aria-live="polite">
          {messages.length === 0 && (
            <p className="agents-empty">
              Try a scenario above or type a financial question. Non-financial topics are blocked so
              guidance stays on wealth planning.
            </p>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              className={`agents-msg agents-msg--${m.role}${m.guardrail ? ' agents-msg--guard' : ''}`}
            >
              {m.role === 'user' && m.text && <p className="agents-msg-text">{m.text}</p>}
              {m.role === 'assistant' && m.text && <p className="agents-msg-text">{m.text}</p>}
              {m.role === 'assistant' && m.plan && <PlanCard plan={m.plan} />}
            </div>
          ))}
        </div>

        <form className="agents-composer" onSubmit={onSubmit}>
          <div className="agents-composer-inner">
            <label htmlFor="agent-prompt" className="sr-only">
              Message to agent
            </label>
            <input
              id="agent-prompt"
              className="agents-input"
              placeholder="Define a task for your agent"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              autoComplete="off"
            />
            <button type="submit" className="agents-send" aria-label="Send message">
              ↑
            </button>
          </div>
        </form>

        <p className="agents-footer-note">
          Instead of manually monitoring markets and placing every trade yourself, you can describe a
          situation here and get a transparent, step-by-step rebalancing outline. Complex ideas are
          translated into simple logic; always confirm costs and taxes with your broker and tax
          advisor before acting.
        </p>
      </div>
    </div>
  )
}
