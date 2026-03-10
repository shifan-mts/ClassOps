import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";

export default function App() {
  const [qPaperTopic, setQPaperTopic] = useState("");
  const [generatedPaper, setGeneratedPaper] = useState("");

  const handleGoogleSync = () => {
    window.location.href = "http://localhost:5000/api/auth/google";
  };

  const generatePaper = async () => {
    const res = await fetch("http://localhost:5000/api/question-paper/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: qPaperTopic, difficulty: "Hard" })
    });
    const data = await res.json();
    setGeneratedPaper(data.question_paper);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">EduSync OS</h1>
          <p className="text-slate-500">Teacher Workflow Automation Dashboard</p>
        </div>
        <Button onClick={handleGoogleSync} className="bg-blue-600 hover:bg-blue-700">
          Sync with Google Classroom
        </Button>
      </header>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview & Targets</TabsTrigger>
          <TabsTrigger value="attendance">Attendance</TabsTrigger>
          <TabsTrigger value="ai-tools">AI Tools (Q-Paper & Plagiarism)</TabsTrigger>
          <TabsTrigger value="timetable">Timetable</TabsTrigger>
        </TabsList>

        {/* OVERVIEW TAB */}
        <TabsContent value="overview" className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Material & Target Completion</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                <li className="flex justify-between items-center bg-white p-3 rounded shadow-sm border">
                  <span>Unit 1: Data Structures</span>
                  <span className="text-green-600 text-sm font-bold">Completed</span>
                </li>
                <li className="flex justify-between items-center bg-white p-3 rounded shadow-sm border">
                  <span>Unit 2: Algorithms</span>
                  <span className="text-orange-500 text-sm font-bold">Pending (Due: Oct 12)</span>
                </li>
              </ul>
              <Button className="mt-4 w-full" variant="outline">+ Add Syllabus Target</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>NBA/NAAC Metrics Data</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500 mb-4">Export mapped Course Outcomes (CO) & Program Outcomes (PO) directly to Excel for COE submission.</p>
              <Button className="w-full">Generate NBA Compliance Report</Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI TOOLS TAB */}
        <TabsContent value="ai-tools" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Bloom's Taxonomy Question Paper Generator</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex space-x-2 mb-4">
                <Input
                  placeholder="Enter Topic (e.g., Operating Systems)"
                  value={qPaperTopic}
                  onChange={(e) => setQPaperTopic(e.target.value)}
                />
                <Button onClick={generatePaper}>Generate</Button>
              </div>
              {generatedPaper && (
                <div className="bg-gray-100 p-4 rounded whitespace-pre-wrap font-mono text-sm h-64 overflow-y-auto">
                  {generatedPaper}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* OTHER TABS (Placeholders for Dev 4) */}
        <TabsContent value="attendance">
          <Card><CardContent className="pt-6">Attendance Tracker UI goes here...</CardContent></Card>
        </TabsContent>
        <TabsContent value="timetable">
          <Card><CardContent className="pt-6">Timetable Grid UI goes here...</CardContent></Card>
        </TabsContent>

      </Tabs>
    </div>
  );
}