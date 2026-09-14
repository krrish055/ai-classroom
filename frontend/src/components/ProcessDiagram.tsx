import {
  Activity,
  Building2,
  Cpu,
  Gauge,
  Leaf,
  Power,
  Shield,
  Workflow,
  Zap,
  type LucideIcon,
} from "lucide-react";
import type { SlideCard } from "../services/slideFromSegment";

const TONES = ["gold", "mint", "sky"] as const;

const FALLBACK: LucideIcon[] = [Zap, Shield, Activity, Cpu, Gauge, Power, Workflow, Building2, Leaf];

function iconFor(label: string, index: number): LucideIcon {
  const text = label.toLowerCase();
  if (/protect|safe|shield|margin/.test(text)) return Shield;
  if (/trip|break|cut|power|overload/.test(text)) return Zap;
  if (/current|flow|circuit|wire|load/.test(text)) return Activity;
  if (/measure|sense|detect|gauge/.test(text)) return Gauge;
  if (/system|board|chip|logic/.test(text)) return Cpu;
  if (/build|struct|plant/.test(text)) return Building2;
  if (/green|leaf|eco/.test(text)) return Leaf;
  if (/on|off|switch|supply/.test(text)) return Power;
  if (/process|step|flow|path/.test(text)) return Workflow;
  return FALLBACK[index % FALLBACK.length];
}

type ProcessDiagramProps = {
  cards: SlideCard[];
  flow: string[];
  activeCard: number;
  presenting: boolean;
  speaking: boolean;
};

export function ProcessDiagram({ cards, flow, activeCard, presenting, speaking }: ProcessDiagramProps) {
  const nodes = cards.slice(0, 3);
  if (!nodes.length) return null;

  const highlight = activeCard >= 0;

  return (
    <div className={`diagram ${presenting ? "is-live" : ""} ${speaking ? "is-speaking" : ""}`}>
      <div className="diagram-glow" />
      <svg className="diagram-mesh" viewBox="0 0 800 280" preserveAspectRatio="none">
        <defs>
          <linearGradient id="meshStroke" x1="0" x2="1">
            <stop offset="0%" stopColor="#e8a36a" stopOpacity="0.18" />
            <stop offset="50%" stopColor="#5b6bd6" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#3caf7a" stopOpacity="0.18" />
          </linearGradient>
        </defs>
        <path d="M40 140 C 180 40, 320 240, 400 140 S 620 40, 760 140" fill="none" stroke="url(#meshStroke)" strokeWidth="2" />
        <path d="M60 200 C 220 90, 360 230, 520 120 S 700 210, 760 80" fill="none" stroke="url(#meshStroke)" strokeWidth="1.2" />
      </svg>

      <ol className={`diagram-track ${highlight ? "has-active" : ""}`}>
        {nodes.map((card, index) => {
          const Icon = iconFor(`${card.label} ${card.hint}`, index);
          const isActive = highlight && index === activeCard;
          const isDone = highlight && index < activeCard;
          const connector = index < nodes.length - 1 ? flow[index] || "" : "";
          return (
            <li key={`${card.label}-${index}`} className="diagram-step">
              <article
                className={`diagram-node tone-${TONES[index % TONES.length]} ${isActive ? "active" : ""} ${isDone ? "done" : ""}`}
                style={{ animationDelay: `${index * 120}ms` }}
              >
                <span className="diagram-index">{String(index + 1).padStart(2, "0")}</span>
                <span className="diagram-icon">
                  <span className="diagram-pulse" />
                  <Icon size={34} strokeWidth={1.7} />
                </span>
                <strong>{card.label}</strong>
                {card.hint ? <span className="diagram-hint">{card.hint}</span> : null}
              </article>

              {index < nodes.length - 1 ? (
                <div className={`diagram-link ${isActive ? "from-active" : ""} ${isDone ? "done" : ""}`}>
                  <span className="diagram-link-rail" />
                  <span className="diagram-link-dot" />
                  {connector ? <em>{connector}</em> : null}
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
