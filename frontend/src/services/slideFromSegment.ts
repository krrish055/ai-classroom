import type { LessonSegment, SlideContent, SlideLayout } from "../types/lesson";

export type SlideCard = {
  label: string;
  hint: string;
};

export type DemoSlideModel = {
  headline: string;
  kicker: string;
  bullets: string[];
  layout: SlideLayout;
  index: number;
  total: number;
};

const IDLE_SLIDE: DemoSlideModel = {
  headline: "Paste a script to build the deck",
  kicker: "Live training demo",
  bullets: [
    "Each spoken line becomes one presentable slide.",
    "The avatar reads your script word for word.",
    "Download the same deck as PPT, PDF, or Word.",
  ],
  layout: "cards",
  index: 0,
  total: 0,
};

export function idleSlide(): DemoSlideModel {
  return IDLE_SLIDE;
}

export function demoFromSegment(
  segment: LessonSegment | undefined,
  lessonTitle: string,
  index: number,
  total: number,
): DemoSlideModel {
  if (!segment) return idleSlide();
  const slide: SlideContent | undefined = segment.slide;
  const bullets = (slide?.bullets || []).map((item) => item.trim()).filter((item) => item.split(/\s+/).length >= 3);
  const headline = (slide?.headline || segment.title || lessonTitle).trim();
  const generic = /^line\s+\d+$/i.test(headline);
  return {
    headline: generic ? lessonTitle || headline : headline,
    kicker: slide?.kicker || lessonTitle || "Live training demo",
    bullets: bullets.slice(0, 3),
    layout: slide?.layout || "cards",
    index,
    total,
  };
}
