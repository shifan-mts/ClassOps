import React from 'react';
import {
    BarChart3,
    TrendingUp,
    Users,
    Target,
    ArrowUpRight,
    ArrowDownRight,
    Download
} from 'lucide-react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    PointElement,
    LineElement,
    RadialLinearScale,
    Filler,
} from 'chart.js';
import { Bar, Line, Radar } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    RadialLinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const Analytics = () => {
    const performanceData = {
        labels: ['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4'],
        datasets: [
            {
                label: 'Average Score',
                data: [78, 82, 75, 88],
                backgroundColor: '#005461',
                borderRadius: 8,
            },
            {
                label: 'Top Score',
                data: [95, 98, 92, 100],
                backgroundColor: '#3BC1A8',
                borderRadius: 8,
            }
        ],
    };

    const trendData = {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
        datasets: [
            {
                label: 'Class Engagement',
                data: [65, 78, 72, 85, 90, 88],
                borderColor: '#0C7779',
                backgroundColor: 'rgba(12, 119, 121, 0.1)',
                fill: true,
                tension: 0.4,
            }
        ]
    };

    const radarData = {
        labels: ['Knowledge', 'Application', 'Analysis', 'Synthesis', 'Evaluation'],
        datasets: [
            {
                label: 'Current Class Profile',
                data: [85, 70, 60, 45, 55],
                backgroundColor: 'rgba(0, 84, 97, 0.2)',
                borderColor: '#005461',
                pointBackgroundColor: '#005461',
            }
        ]
    };

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Performance Analytics</h1>
                    <p className="text-light-text mt-1">Deep dive into class performance and learning outcomes.</p>
                </div>
                <button className="bg-white border border-light-secondary px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-light-bg transition-all text-dark-primary">
                    <Download size={20} />
                    Full Academic Report
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                        <div className="p-3 bg-blue-100 text-blue-600 rounded-2xl">
                            <Target size={24} />
                        </div>
                        <span className="text-green-500 font-bold flex items-center text-xs">
                            <ArrowUpRight size={14} /> +5.2%
                        </span>
                    </div>
                    <h3 className="text-light-text font-medium text-sm">Average CGPA</h3>
                    <p className="text-2xl font-bold text-dark-primary mt-1">3.42</p>
                </div>

                <div className="bg-white p-6 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                        <div className="p-3 bg-red-100 text-red-600 rounded-2xl">
                            <Users size={24} />
                        </div>
                        <span className="text-red-500 font-bold flex items-center text-xs">
                            <ArrowDownRight size={14} /> -2.1%
                        </span>
                    </div>
                    <h3 className="text-light-text font-medium text-sm">Active Engagement</h3>
                    <p className="text-2xl font-bold text-dark-primary mt-1">82%</p>
                </div>

                <div className="bg-white p-6 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                        <div className="p-3 bg-emerald-100 text-emerald-600 rounded-2xl">
                            <TrendingUp size={24} />
                        </div>
                        <span className="text-green-500 font-bold flex items-center text-xs">
                            <ArrowUpRight size={14} /> +12%
                        </span>
                    </div>
                    <h3 className="text-light-text font-medium text-sm">Assignment Completion</h3>
                    <p className="text-2xl font-bold text-dark-primary mt-1">94%</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <h2 className="text-xl font-bold text-dark-primary mb-8">Unit-wise Performance</h2>
                    <div className="h-72">
                        <Bar data={performanceData} options={{ responsive: true, maintainAspectRatio: false, scales: { x: { grid: { display: false } }, y: { grid: { display: false } } } }} />
                    </div>
                </div>

                <div className="bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <h2 className="text-xl font-bold text-dark-primary mb-8">Skill Proficiency (Bloom's)</h2>
                    <div className="h-72 flex justify-center">
                        <Radar data={radarData} options={{ maintainAspectRatio: false }} />
                    </div>
                </div>
            </div>

            <div className="bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm">
                <h2 className="text-xl font-bold text-dark-primary mb-8">Weekly Participation Trend</h2>
                <div className="h-64">
                    <Line data={trendData} options={{ responsive: true, maintainAspectRatio: false, scales: { x: { grid: { display: false } }, y: { grid: { display: false } } } }} />
                </div>
            </div>
        </div>
    );
};

export default Analytics;
