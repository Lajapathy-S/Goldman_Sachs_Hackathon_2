import './AboutPage.css'

export function AboutPage() {
  return (
    <article className="about-page container">
      <h1>About</h1>
      <p className="about-lead">
        This experience is built around the <strong>Goldman Sachs AI application</strong> ethos:
        rigorous finance infrastructure paired with interfaces that feel approachable. The goal is to
        bring institutional-grade clarity to everyday investors — without turning the product into a
        terminal screen full of codes and acronyms.
      </p>
      <section className="about-block">
        <h2>What that means here</h2>
        <p>
          AIChemist (this demo) translates that idea into a focused portfolio surface: you see
          holdings, risk, and next steps in order of importance. Behind the scenes, the same
          principle applies — prioritize transparent assumptions, label uncertainty, and avoid
          overconfidence when markets are noisy.
        </p>
      </section>
      <section className="about-block">
        <h2>For people who are not “market natives”</h2>
        <p>
          You should not need to trade every week to feel in control. The Goldman Sachs AI
          application line of thinking emphasizes decision support: explain the tradeoff, show the
          range of outcomes, then let the human choose. We mirror that with copy, layout, and flows
          tuned for first-time and long-horizon investors alike.
        </p>
      </section>
      <p className="about-note">
        This site is a student / portfolio project and is not affiliated with Goldman Sachs. The
        reference describes the design direction and narrative only.
      </p>
    </article>
  )
}
