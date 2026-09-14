import { convertToExcalidrawElements } from "@excalidraw/excalidraw";
import type { BoardElement } from "../types/lesson";

type SceneElement = { id?: string };

export type ExcalidrawAPI = {
  getSceneElements: () => readonly SceneElement[];
  updateScene: (params: {
    elements?: readonly unknown[];
    appState?: Record<string, unknown>;
  }) => void;
  scrollToContent?: (
    target?: unknown,
    opts?: { fitToContent?: boolean; animate?: boolean },
  ) => void;
};

type Bounds = { x: number; y: number; w: number; h: number };

const BOARD_FRAME = {
  type: "rectangle",
  id: "classroom_frame",
  x: 16,
  y: 8,
  width: 1148,
  height: 704,
  strokeColor: "#94a3b8",
  backgroundColor: "transparent",
  fillStyle: "solid",
  strokeWidth: 2,
  roughness: 0,
};

function toSkeleton(elements: BoardElement[]) {
  const posMap = new Map<string, Bounds>();
  for (const el of elements) {
    if (el.id && ["rectangle", "ellipse", "diamond"].includes(String(el.type))) {
      posMap.set(String(el.id), {
        x: Number(el.x ?? 0),
        y: Number(el.y ?? 0),
        w: Number(el.width || 200),
        h: Number(el.height || 80),
      });
    }
  }

  return elements.map((el, idx) => {
    const skeleton: Record<string, unknown> = {
      type: el.type,
      x: el.x ?? 0,
      y: el.y ?? 0,
      id: el.id || `el_${Date.now()}_${idx}`,
      strokeWidth: el.strokeWidth ?? 2,
      roughness: el.roughness ?? 1,
    };
    if (el.width != null) skeleton.width = el.width;
    if (el.height != null) skeleton.height = el.height;
    if (el.strokeColor) skeleton.strokeColor = el.strokeColor;
    if (el.backgroundColor) {
      skeleton.backgroundColor = el.backgroundColor;
      skeleton.fillStyle = el.fillStyle || "solid";
    }

    if (["rectangle", "ellipse", "diamond"].includes(String(el.type))) {
      const label = el.label as { text?: string } | string | undefined;
      const labelText =
        (typeof label === "object" ? label?.text : label) ||
        el.labelText ||
        el.text;
      if (labelText) {
        skeleton.label = {
          text: String(labelText),
          fontSize: el.fontSize || 18,
          textAlign: "center",
          verticalAlign: "middle",
        };
      }
      if (!skeleton.width) skeleton.width = 200;
      if (!skeleton.height) skeleton.height = 80;
    }

    if (el.type === "text") {
      const label = el.label as { text?: string } | string | undefined;
      skeleton.text =
        el.text ||
        el.labelText ||
        (typeof label === "object" ? label?.text : label) ||
        "";
      if (el.fontSize) skeleton.fontSize = el.fontSize;
    }

    if (el.type === "arrow" || el.type === "line") {
      skeleton.endArrowhead = el.endArrowhead ?? (el.type === "arrow" ? "arrow" : null);
      const label = el.label as { text?: string } | string | undefined;
      const arrowLabel =
        (typeof label === "object" ? label?.text : label) || el.labelText;
      if (arrowLabel) skeleton.label = { text: String(arrowLabel) };

      if (Array.isArray(el.points)) {
        skeleton.points = el.points;
      } else if (el.startId || el.endId) {
        const src = el.startId ? posMap.get(String(el.startId)) : null;
        const dst = el.endId ? posMap.get(String(el.endId)) : null;
        if (src && dst) {
          const srcRight = src.x + src.w;
          const srcCy = src.y + src.h / 2;
          const dstCy = dst.y + dst.h / 2;
          if (dst.x >= srcRight - 12) {
            skeleton.x = srcRight;
            skeleton.y = srcCy;
            skeleton.points = [
              [0, 0],
              [dst.x - srcRight, dstCy - srcCy],
            ];
          } else {
            const srcCx = src.x + src.w / 2;
            skeleton.x = srcCx;
            skeleton.y = src.y + src.h;
            skeleton.points = [
              [0, 0],
              [dst.x + dst.w / 2 - srcCx, dst.y - (src.y + src.h)],
            ];
          }
        } else {
          skeleton.points = [
            [0, 0],
            [Number(el.width || 120), Number(el.height || 0)],
          ];
        }
      } else {
        skeleton.points = [
          [0, 0],
          [Number(el.width || 120), Number(el.height || 0)],
        ];
      }
    }

    return skeleton;
  });
}

export function frameClassroom(api: ExcalidrawAPI) {
  const frame = api.getSceneElements().find((el) => el.id === "classroom_frame");
  if (frame) {
    api.scrollToContent?.(frame, { fitToContent: true, animate: false });
    return;
  }
  api.scrollToContent?.(undefined, { fitToContent: true, animate: false });
}

export function drawBoard(
  api: ExcalidrawAPI,
  elements: BoardElement[],
  reset: boolean,
) {
  if (!elements.length && !reset) return;
  const payload = reset ? [BOARD_FRAME, ...toSkeleton(elements)] : toSkeleton(elements);
  const converted = convertToExcalidrawElements(payload as any, {
    regenerateIds: false,
  });
  const existing = reset ? [] : api.getSceneElements();
  api.updateScene({ elements: [...existing, ...converted] });
}
