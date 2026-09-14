import { useState } from "react";
import ClassroomPage from "./pages/ClassroomPage";
import LandingPage from "./pages/LandingPage";

export default function App() {
  const [started, setStarted] = useState(false);
  if (!started) return <LandingPage onStart={() => setStarted(true)} />;
  return <ClassroomPage />;
}
