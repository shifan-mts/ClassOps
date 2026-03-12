const fs = require('fs');
const path = 'Frontend/src/App.jsx';
let c = fs.readFileSync(path, 'utf8');

const replaceOrThrow = (pattern, replacement, label) => {
  const next = c.replace(pattern, replacement);
  if (next === c) {
    throw new Error(`Pattern not found: ${label}`);
  }
  c = next;
};

// Trim key before use in updateServerKey
replaceOrThrow('if (!customApiKey) {', 'if (!customApiKey.trim()) {', 'trim check in updateServerKey');
replaceOrThrow('body: JSON.stringify({ api_key: customApiKey })', 'body: JSON.stringify({ api_key: customApiKey.trim() })', 'trim key in updateServerKey');

// Refresh courses after classroom sync
replaceOrThrow(
`      if (res.ok) {\n        setCourses(Array.isArray(data.courses) ? data.courses : []);\n        alert("Courses synced successfully!");\n      } else {`,
`      if (res.ok) {\n        await fetchCourses();\n        alert("Courses synced successfully!");\n      } else {`,
'refresh courses after sync'
);

// Build payload with optional API key
const oldFetchBlock =
`      const res = await fetch(\`${API_BASE}/api/question-paper/generate\`, {\n` +
`        method: "POST",\n` +
`        headers: { "Content-Type": "application/json" },\n` +
`        body: JSON.stringify({ \n` +
`          topic: qPaperTopic, \n` +
`          difficulty: "Medium",\n` +
`          course_name: courseName,\n` +
`          api_key: customApiKey\n` +
`        })\n` +
`      });`;

const newFetchBlock =
`      const payload = { topic: qPaperTopic, difficulty: "Medium", course_name: courseName };\n` +
`      const trimmedKey = customApiKey.trim();\n` +
`      if (trimmedKey) {\n` +
`        payload.api_key = trimmedKey;\n` +
`      }\n` +
`      const res = await fetch(\`${API_BASE}/api/question-paper/generate\`, {\n` +
`        method: "POST",\n` +
`        headers: { "Content-Type": "application/json" },\n` +
`        body: JSON.stringify(payload)\n` +
`      });`;

replaceOrThrow(oldFetchBlock, newFetchBlock, 'question paper payload');

// Broaden error handling for API key issues
replaceOrThrow(
`      if (!res.ok) {\n        if (res.status === 429 || (data.error && data.error.toLowerCase().includes("quota"))) {\n          setIsQuotaExceeded(true);\n        }\n        throw new Error(data?.error || \`Request failed with status ${res.status}\`);\n      }`,
`      if (!res.ok) {\n        const errText = (data?.error || "").toLowerCase();\n        if (res.status === 429 || res.status === 401 || errText.includes("quota") || errText.includes("api key") || errText.includes("invalid")) {\n          setIsQuotaExceeded(true);\n        }\n        throw new Error(data?.error || \`Request failed with status ${res.status}\`);\n      }`,
'expand AI error handling'
);

// Clear the key warning on success
replaceOrThrow(
`      const content = data?.question_paper || data?.questionPaper || "No question paper returned.";\n      setGeneratedPaper(content);\n      setError("");`,
`      const content = data?.question_paper || data?.questionPaper || "No question paper returned.";\n      setGeneratedPaper(content);\n      setError("");\n      setIsQuotaExceeded(false);`,
'clear quota flag on success'
);

fs.writeFileSync(path, c, 'utf8');
