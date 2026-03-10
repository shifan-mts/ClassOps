import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Courses from './pages/Courses';
import Students from './pages/Students';
import Attendance from './pages/Attendance';
import Assignments from './pages/Assignments';
import Analytics from './pages/Analytics';
import QuestionGenerator from './pages/QuestionGenerator';
import Reports from './pages/Reports';
import Login from './pages/Login';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<Layout />}>
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="courses" element={<Courses />} />
                    <Route path="students" element={<Students />} />
                    <Route path="attendance" element={<Attendance />} />
                    <Route path="assignments" element={<Assignments />} />
                    <Route path="analytics" element={<Analytics />} />
                    <Route path="question-generator" element={<QuestionGenerator />} />
                    <Route path="reports" element={<Reports />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
