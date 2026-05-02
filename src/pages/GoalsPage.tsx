import { useState } from 'react'
import './GoalsPage.css'

const STORAGE_KEY = 'aichemist_goal_profile'

type Step = 0 | 1 | 2 | 3 | 4

export function GoalsPage() {
  const [step, setStep] = useState<Step>(0)
  const [mainGoal, setMainGoal] = useState('')
  const [years, setYears] = useState(15)
  const [comfort, setComfort] = useState<'sell' | 'hold' | 'buy'>('hold')

  const riskLabel =
    comfort === 'sell' ? 'Cautious (prefers smaller swings)' : comfort === 'hold' ? 'Balanced' : 'Growth-minded'

  function save() {
    const profile = {
      mainGoal,
      years,
      comfort,
      riskLabel,
      savedAt: new Date().toISOString(),
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
    setStep(4)
  }

  return (
    <div className="goals-page">
      <div className="goals-inner">
        <header className="goals-head">
          <h1>Guided goal-setting</h1>
          <p className="goals-lead">
            A few plain questions — no Greek letters, no “alpha/beta” homework. We translate your
            answers into a simple risk label you can use with the AI rebalance tool.
          </p>
        </header>

        {step === 0 && (
          <section className="goals-card">
            <h2>Welcome</h2>
            <p>
              Most people don’t need complicated ratios to start. They need clarity on{' '}
              <strong>when</strong> they need the money and <strong>how bumpy</strong> a ride they
              can stomach.
            </p>
            <button type="button" className="goals-btn primary" onClick={() => setStep(1)}>
              Begin
            </button>
          </section>
        )}

        {step === 1 && (
          <section className="goals-card">
            <h2>What is this money mainly for?</h2>
            <div className="goals-options">
              {[
                ['retirement', 'Long-term / retirement'],
                ['home', 'A large purchase (home, education, etc.)'],
                ['emergency', 'Safety net / emergency fund'],
                ['growth', 'General long-term growth'],
              ].map(([id, label]) => (
                <label key={id} className="goals-radio">
                  <input
                    type="radio"
                    name="goal"
                    checked={mainGoal === id}
                    onChange={() => setMainGoal(id)}
                  />
                  <span>{label}</span>
                </label>
              ))}
            </div>
            <div className="goals-actions">
              <button type="button" className="goals-btn ghost" onClick={() => setStep(0)}>
                Back
              </button>
              <button
                type="button"
                className="goals-btn primary"
                disabled={!mainGoal}
                onClick={() => setStep(2)}
              >
                Next
              </button>
            </div>
          </section>
        )}

        {step === 2 && (
          <section className="goals-card">
            <h2>Roughly when will you need most of this money?</h2>
            <p className="goals-hint">Slide to the nearest few years — perfection isn’t required.</p>
            <div className="goals-years">
              <input
                type="range"
                min={1}
                max={40}
                value={years}
                onChange={(e) => setYears(Number(e.target.value))}
              />
              <p className="goals-years-val">
                About <strong>{years}</strong> {years === 1 ? 'year' : 'years'}
              </p>
            </div>
            <div className="goals-actions">
              <button type="button" className="goals-btn ghost" onClick={() => setStep(1)}>
                Back
              </button>
              <button type="button" className="goals-btn primary" onClick={() => setStep(3)}>
                Next
              </button>
            </div>
          </section>
        )}

        {step === 3 && (
          <section className="goals-card">
            <h2>If your portfolio dropped about 20% in a tough year, you would…</h2>
            <div className="goals-options">
              <label className="goals-radio">
                <input
                  type="radio"
                  name="comfort"
                  checked={comfort === 'sell'}
                  onChange={() => setComfort('sell')}
                />
                <span>Move mostly to safer options — sleep matters most.</span>
              </label>
              <label className="goals-radio">
                <input
                  type="radio"
                  name="comfort"
                  checked={comfort === 'hold'}
                  onChange={() => setComfort('hold')}
                />
                <span>Hold steady and stick to the plan.</span>
              </label>
              <label className="goals-radio">
                <input
                  type="radio"
                  name="comfort"
                  checked={comfort === 'buy'}
                  onChange={() => setComfort('buy')}
                />
                <span>Try to add a little if I can — I accept more bumpiness.</span>
              </label>
            </div>
            <div className="goals-actions">
              <button type="button" className="goals-btn ghost" onClick={() => setStep(2)}>
                Back
              </button>
              <button type="button" className="goals-btn primary" onClick={save}>
                Save profile
              </button>
            </div>
          </section>
        )}

        {step === 4 && (
          <section className="goals-card success">
            <h2>You’re set</h2>
            <p>
              We saved a simple profile: goal{' '}
              <strong>
                {mainGoal === 'retirement'
                  ? 'Long-term / retirement'
                  : mainGoal === 'home'
                    ? 'Large purchase'
                    : mainGoal === 'emergency'
                      ? 'Safety net'
                      : mainGoal === 'growth'
                        ? 'General growth'
                        : mainGoal}
              </strong>
              , horizon <strong>{years} yr</strong>, comfort style <strong>{riskLabel}</strong>.
            </p>
            <p className="goals-next">
              Next: open <strong>AI Rebalance</strong>, enter placeholder holdings, pick a “what-if”
              story — the assistant will keep language beginner-friendly.
            </p>
            <button type="button" className="goals-btn ghost" onClick={() => setStep(0)}>
              Start over
            </button>
          </section>
        )}
      </div>
    </div>
  )
}
