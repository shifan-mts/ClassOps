import React from 'react';
import {
    Users,
    BookOpen,
    AlertTriangle,
    CheckCircle2,
    Clock,
    TrendingUp,
    ArrowUpRight,
    MoreVertical
} from 'lucide-react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    PointElement,
    LineElement,
    Filler,
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const StatCard = ({ title, value, subtext, icon: Icon, color, trend }) => (
    <div className="bg-white p-6 rounded-3xl border border-light-secondary/50 shadow-sm hover:shadow-md transition-all group">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-2xl ${color} bg-opacity-10 text-${color.split('-')[1]}-600 group-hover:scale-110 transition-transform`}>
                <Icon size={24} />
            </div>
            {trend && (
                <span className={`flex items-center gap-1 text-xs font-bold ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {trend > 0 ? '+' : ''}{trend}%
                    <TrendingUp size={14} className={trend < 0 ? 'rotate-180' : ''} />
                </span>
            )}
        </div>
        <h3 className="text-light-text font-medium text-sm">{title}</h3>
        <div className="flex items-baseline gap-2 mt-1">
            <p className="text-2xl font-bold text-dark-primary">{value}</p>
            <p className="text-xs text-light-text/60">{subtext}</p>
        </div>
    </div>
);

const Dashboard = () => {
    const barData = {
        labels: ['Unit 1', 'Unit 2', 'Unit 3', 'Unit 4', 'Unit 5'],
        datasets: [
            {
                label: 'Syllabus Completion %',
                data: [100, 100, 75, 20, 0],
                backgroundColor: '#3BC1A8',
                borderRadius: 8,
            },
        ],
    };

    const lineData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        datasets: [
            {
                fill: true,
                label: 'Attendance Rate',
                data: [85, 92, 88, 95, 89],
                borderColor: '#005461',
                backgroundColor: 'rgba(0, 84, 97, 0.1)',
                tension: 0.4,
            },
        ],
    };

    const donutData = {
        labels: ['High Risk', 'Medium Risk', 'Low Risk'],
        datasets: [
            {
                data: [5, 12, 83],
                backgroundColor: ['#EF4444', '#F59E0B', '#10B981'],
                borderWidth: 0,
                cutout: '70%',
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: { display: false },
        },
        scales: {
            y: { beginAtZero: true, grid: { display: false } },
            x: { grid: { display: false } },
        },
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Good Morning, Dr. Wilson</h1>
                    <p className="text-light-text mt-1">Here is what's happening with your classes today.</p>
                </div>
                <div className="flex gap-3">
                    <button className="bg-white px-4 py-2 rounded-xl text-dark-primary font-semibold text-sm border border-light-secondary flex items-center gap-2 hover:bg-light-bg transition-all">
                        <Clock size={18} />
                        Schedule
                    </button>
                    <button className="bg-dark-primary text-white px-4 py-2 rounded-xl font-semibold text-sm flex items-center gap-2 hover:bg-dark-secondary transition-all shadow-lg shadow-dark-primary/20">
                        Export Report
                        <ArrowUpRight size={18} />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Today's Classes"
                    value="4"
                    subtext="Next: Data Structures @ 10:00 AM"
                    icon={BookOpen}
                    color="bg-blue-500"
                />
                <StatCard
                    title="Attendance Alerts"
                    value="12"
                    subtext="Students below 75%"
                    icon={AlertTriangle}
                    color="bg-red-500"
                    trend={-2}
                />
                <StatCard
                    title="Weak Students"
                    value="8"
                    subtext="Need academic support"
                    icon={Users}
                    color="bg-orange-500"
                />
                <StatCard
                    title="Pending Gradings"
                    value="45"
                    subtext="Across 3 assignments"
                    icon={CheckCircle2}
                    color="bg-green-500"
                    trend={15}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <div className="flex justify-between items-center mb-8">
                        <h2 className="text-xl font-bold text-dark-primary">Weekly Attendance Flow</h2>
                        <select className="bg-light-bg text-sm font-medium px-3 py-1 rounded-lg border-none outline-none">
                            <option>Data Structures (CS-302)</option>
                            <option>Algorithms (CS-401)</option>
                        </select>
                    </div>
                    <div className="h-64">
                        <Line data={lineData} options={chartOptions} />
                    </div>
                </div>

                <div className="bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <h2 className="text-xl font-bold text-dark-primary mb-2">Student Risk Profile</h2>
                    <p className="text-light-text text-sm mb-6">Based on marks & attendance</p>
                    <div className="h-48 relative flex items-center justify-center">
                        <Doughnut data={donutData} />
                        <div className="absolute text-center">
                            <p className="text-2xl font-bold text-dark-primary">100</p>
                            <p className="text-[10px] text-light-text uppercase tracking-widest font-bold">Total Students</p>
                        </div>
                    </div>
                    <div className="mt-6 space-y-3">
                        <div className="flex justify-between items-center text-sm">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                <span className="text-light-text">Low Risk</span>
                            </div>
                            <span className="font-bold text-dark-primary">83%</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                                <span className="text-light-text">Medium Risk</span>
                            </div>
                            <span className="font-bold text-dark-primary">12%</span>
                        </div>
                        <div className="flex justify-between items-center text-sm">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                                <span className="text-light-text">High Risk</span>
                            </div>
                            <span className="font-bold text-dark-primary">5%</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm">
                    <h2 className="text-xl font-bold text-dark-primary mb-6">Syllabus Progress Tracker</h2>
                    <div className="h-64">
                        <Bar data={barData} options={chartOptions} />
                    </div>
                </div>

                <div className="bg-white p-8 rounded-3xl border border-light-secondary/50 shadow-sm overflow-hidden">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold text-dark-primary">Recent Activity</h2>
                        <button className="text-dark-accent text-sm font-bold hover:underline">View All</button>
                    </div>
                    <div className="space-y-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex gap-4 items-start group cursor-pointer">
                                <div className="w-10 h-10 rounded-xl bg-light-bg flex items-center justify-center text-dark-secondary group-hover:bg-dark-highlight group-hover:text-dark-primary transition-all">
                                    <Clock size={18} />
                                </div>
                                <div className="flex-1 border-b border-light-secondary/50 pb-4">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <p className="text-sm font-bold text-dark-primary">Attendance submission</p>
                                            <p className="text-xs text-light-text mt-1">CS-302 (Unit 2) marked for 45 students</p>
                                        </div>
                                        <span className="text-[10px] bg-light-bg px-2 py-1 rounded-md text-light-text font-bold">2H AGO</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
