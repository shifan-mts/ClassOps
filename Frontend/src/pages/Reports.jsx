import React from 'react';
import { FileBarChart, Download, FileText, PieChart, Table, CheckCircle, ArrowRight } from 'lucide-react';

const ReportItem = ({ title, description, icon: Icon, color }) => (
    <div className="bg-white p-8 rounded-[32px] border border-light-secondary/50 shadow-sm hover:shadow-xl transition-all group flex flex-col h-full">
        <div className={`w-14 h-14 rounded-2xl ${color} flex items-center justify-center text-white mb-6 shadow-lg shadow-current/10 group-hover:scale-110 transition-transform`}>
            <Icon size={28} />
        </div>

        <h3 className="text-xl font-bold text-dark-primary mb-2">{title}</h3>
        <p className="text-sm text-light-text mb-8 flex-1 leading-relaxed">{description}</p>

        <div className="pt-6 border-t border-light-secondary/30 flex items-center justify-between mt-auto">
            <div className="flex gap-2">
                <button className="p-3 bg-light-bg text-dark-primary rounded-xl hover:bg-dark-highlight transition-all" title="Download PDF">
                    <FileText size={18} />
                </button>
                <button className="p-3 bg-light-bg text-dark-primary rounded-xl hover:bg-dark-highlight transition-all" title="Download Excel">
                    <Table size={18} />
                </button>
            </div>
            <button className="px-5 py-3 bg-dark-primary text-white text-sm font-bold rounded-xl hover:bg-dark-secondary transition-all flex items-center gap-2">
                Generate
                <ArrowRight size={16} />
            </button>
        </div>
    </div>
);

const Reports = () => {
    const reports = [
        {
            title: 'Course Outcome Attainment',
            description: 'Detailed analysis of CO attainment based on continuous evaluation and end-semester results.',
            icon: CheckCircle,
            color: 'bg-emerald-600'
        },
        {
            title: 'Marks Distribution (NBA)',
            description: 'Accreditation-ready reports showing bell curve and grade statistics for individual subjects.',
            icon: FileBarChart,
            color: 'bg-blue-600'
        },
        {
            title: 'Attendance Risk Summary',
            description: 'Comprehensive list of students failing the 75% attendance threshold across all subjects.',
            icon: PieChart,
            color: 'bg-red-600'
        },
        {
            title: 'Program Summary Report',
            description: 'Overview of syllabus completion, average performance, and faculty workload for the current semester.',
            icon: FileText,
            color: 'bg-dark-accent'
        }
    ];

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-700">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Accreditation Reports</h1>
                    <p className="text-light-text mt-1">Export data for NBA, NAAC, and internal quality audits.</p>
                </div>
                <div className="flex gap-3">
                    <select className="bg-white border border-light-secondary px-4 py-3 rounded-xl font-semibold text-sm outline-none cursor-pointer">
                        <option>Academic Year 2024-25</option>
                        <option>Academic Year 2023-24</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {reports.map((report, i) => (
                    <ReportItem key={i} {...report} />
                ))}
            </div>

            <div className="bg-dark-primary text-white p-10 rounded-[40px] flex items-center justify-between overflow-hidden relative">
                <div className="relative z-10 space-y-4 max-w-xl">
                    <h2 className="text-2xl font-bold">Custom Report Builder</h2>
                    <p className="text-white/70">Can't find what you're looking for? Create a custom report by selecting specific data points and date ranges.</p>
                    <button className="bg-dark-highlight text-dark-primary px-8 py-4 rounded-2xl font-bold hover:bg-white transition-all shadow-xl shadow-black/20">
                        Open Builder
                    </button>
                </div>
                <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -mr-20 -mt-20 blur-3xl"></div>
                <div className="absolute bottom-0 right-0 w-48 h-48 bg-dark-highlight/20 rounded-full mr-10 -mb-10 blur-2xl"></div>
                <Download size={120} className="text-white/5 relative z-10 -mr-4 rotate-12" />
            </div>
        </div>
    );
};

export default Reports;
