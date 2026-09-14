export type SlideLayout = "title" | "cards" | "steps" | "bullets";

export type SlideContent = {
  headline: string;
  kicker: string;
  bullets: string[];
  layout: SlideLayout;
};

export type BoardElement = Record<string, unknown> & {
  id: string;
  type: string;
};

export type LessonSegment = {
  id: string;
  title: string;
  speech: string;
  board: {
    mode: "replace" | "append";
    elements: BoardElement[];
  };
  slide?: SlideContent;
};

export type Lesson = {
  title: string;
  topic: string;
  level: string;
  language: string;
  segments: LessonSegment[];
};

export type PublicConfig = {
  appName: string;
  ttsProvider: string;
  sttProvider: string;
  speechRate: number;
  demoScript: string;
  avatarEnabled: boolean;
  avatarModule: string;
  maxQueryChars: number;
  maxScriptLines?: number;
  sttLanguage?: string;
};
