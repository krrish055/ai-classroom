import { useEffect, useState } from "react";
import { displayName, studioTitle } from "../lib/brand";
import { getPublicConfig } from "../services/api";

export default function LandingPage({ onStart }: { onStart: () => void }) {
  const [brand, setBrand] = useState("");

  useEffect(() => {
    getPublicConfig()
      .then((cfg) => {
        const name = displayName(cfg);
        setBrand(name);
        document.title = studioTitle(name);
      })
      .catch(() => {
        document.title = studioTitle("");
      });
  }, []);

  return (
    <div className="landing">
      <header className="landing-nav">
        {brand ? <span className="brand-mark">{brand}</span> : <span />}
        <button className="primary-btn" onClick={onStart}>
          Open classroom
        </button>
      </header>
      <main className="landing-hero">
        <p className="eyebrow">AI training studio</p>
        <h1>You write the lines. The avatar presents the slides.</h1>
        <p className="lead">
          Paste a script. Every word is spoken, a clean training slide appears, and a face lip-syncs to the same audio.
        </p>
        <button className="primary-btn large" onClick={onStart}>
          Start presenting
        </button>
        <ul className="landing-points">
          <li>Spoken text is your script, not an LLM rewrite</li>
          <li>Each line becomes a training slide with captions</li>
          <li>Circular avatar lip-syncs to the same audio</li>
        </ul>
      </main>
    </div>
  );
}
