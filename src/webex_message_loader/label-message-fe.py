import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress"; // For confidence display

export default function ThreadLabeler() {
  const [threads, setThreads] = useState({});
  const [selectedLabels, setSelectedLabels] = useState({});
  const [selectedSolutions, setSelectedSolutions] = useState({});

  useEffect(() => {
    fetch("/threads/unlabeled")
      .then((res) => res.json())
      .then((data) => setThreads(data));
  }, []);

  const handleLabelChange = (threadId, label) => {
    setSelectedLabels({ ...selectedLabels, [threadId]: label });
  };

  const handleSolutionSelect = (threadId, messageId) => {
    setSelectedSolutions({ ...selectedSolutions, [threadId]: messageId });
  };

  const handleSubmit = async (threadId) => {
    await fetch("/threads/label", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: threadId,
        topic_label: selectedLabels[threadId] || threads[threadId].predicted_label,
        solution_message_id: selectedSolutions[threadId] || threads[threadId].predicted_solution,
        solution_confidence: threads[threadId].confidence || 1.0,
      }),
    });

    setThreads((prev) => {
      const newThreads = { ...prev };
      delete newThreads[threadId];
      return newThreads;
    });
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">AI-Powered Thread Labeling</h1>
      {Object.entries(threads).map(([threadId, threadData]) => (
        <Card key={threadId} className="mb-4">
          <CardContent>
            <h2 className="text-lg font-semibold">Thread ID: {threadId}</h2>
            {threadData.messages.map((msg) => (
              <div key={msg.message_id} className="p-2 border-b">
                <p><strong>{msg.email}</strong>: {msg.text}</p>
                {msg.message_id === threadData.predicted_solution && (
                  <div className="mt-2">
                    <p className="text-green-600 font-bold">AI Suggested Solution</p>
                    <Progress value={threadData.confidence * 100} className="w-full h-2" />
                  </div>
                )}
              </div>
            ))}
            <p><strong>AI Suggested Label:</strong> {threadData.predicted_label}</p>
            <Button onClick={() => handleSubmit(threadId)}>Confirm & Save</Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
