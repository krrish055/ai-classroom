import { CheckCircle2, Layers3, Sparkles, Workflow } from "lucide-react";
import { demoFromSegment, idleSlide, type DemoSlideModel } from "../services/slideFromSegment";
import type { LessonSegment } from "../types/lesson";

const ICONS = [Sparkles, Layers3, Workflow, CheckCircle2];

type LessonSlideProps = {
  segment?: LessonSegment;
  lessonTitle?: string;
  index?: number;
  total?: number;
  caption: string;
  presenting?: boolean;
  speaking?: boolean;
};

export function LessonSlide({
  segment,
  lessonTitle = "Training",
  index = 0,
  total = 0,
  caption,
  presenting = false,
  speaking = false,
}: LessonSlideProps) {
  const slide: DemoSlideModel = segment
    ? demoFromSegment(segment, lessonTitle, index, total)
    : idleSlide();
  const layout = slide.layout || "cards";
  const progress = slide.total > 0 ? `${slide.index + 1} / ${slide.total}` : "";

  return (
    <div
      key={segment?.id || "idle"}
      className={`demo-slide layout-${layout} ${presenting ? "is-presenting" : ""} ${speaking ? "is-speaking" : ""}`}
    >
      <header className="demo-heading">
        <div className="demo-meta">
          <p className="demo-kicker">{slide.kicker}</p>
          {progress ? <p className="demo-progress">{progress}</p> : null}
        </div>
        <h2>{slide.headline}</h2>
      </header>

      {layout === "steps" ? (
        <ol className="demo-steps">
          {slide.bullets.map((bullet, i) => (
            <li key={bullet} style={{ animationDelay: `${i * 140}ms` }}>
              <span>{String(i + 1).padStart(2, "0")}</span>
              <p>{bullet}</p>
            </li>
          ))}
        </ol>
      ) : layout === "bullets" ? (
        <ul className="demo-bullets">
          {slide.bullets.map((bullet, i) => (
            <li key={bullet} style={{ animationDelay: `${i * 140}ms` }}>
              {bullet}
            </li>
          ))}
        </ul>
      ) : (
        <ol className="demo-cards">
          {slide.bullets.map((bullet, i) => {
            const Icon = ICONS[i % ICONS.length];
            return (
              <li key={bullet} className={`tone-${["gold", "mint", "sky"][i % 3]}`} style={{ animationDelay: `${i * 160}ms` }}>
                <span className="demo-card-index">{String(i + 1).padStart(2, "0")}</span>
                <span className="demo-card-icon">
                  <Icon size={22} strokeWidth={1.8} />
                </span>
                <p>{bullet}</p>
              </li>
            );
          })}
        </ol>
      )}

      {caption ? (
        <p className="sop-caption">
          <span>{caption}</span>
        </p>
      ) : null}
    </div>
  );
}
