import { useState } from "react";
import { api } from "../api/client";

export default function InsightsPanel() {
  const [insight, setInsight] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchInsight = async () => {
    setLoading(true);
    try {
      const data = await api.post("/insights/generate", {});
      setInsight(data.insight);
    } catch (e) {
      setInsight("Could not generate insight. Check your OpenAI key.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card insights-panel">
      <h2>🤖 AI Weekly Insights</h2>
      <button onClick={fetchInsight} disabled={loading}>
        {loading ? "Generating..." : "Generate This Week's Insight"}
      </button>
      {insight && (
        <div className="insight-text">
          {insight.split("\n").map((line, i) => <p key={i}>{line}</p>)}
        </div>
      )}
    </div>
  );
}