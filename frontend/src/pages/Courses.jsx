import React from 'react';
import { Search, Plus, MoreHorizontal, BookOpen, Users, Clock } from 'lucide-react';

const CourseCard = ({ course }) => (
    <div className="bg-white rounded-3xl border border-light-secondary/50 shadow-sm hover:shadow-md transition-all p-6 relative group">
        <button className="absolute top-6 right-6 p-2 text-light-text hover:bg-light-bg rounded-lg transition-colors opacity-0 group-hover:opacity-100">
            <MoreHorizontal size={20} />
        </button>

        <div className={`w-12 h-12 rounded-2xl ${course.color} flex items-center justify-center text-white mb-6 shadow-lg shadow-current/10`}>
            <BookOpen size={24} />
        </div>

        <h3 className="text-xl font-bold text-dark-primary">{course.course_name}</h3>
        <p className="text-sm font-semibold text-dark-accent mt-1">{course.course_code}</p>

        <div className="mt-8 space-y-4">
            <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-light-text">
                    <Users size={16} />
                    <span>Students</span>
                </div>
                <span className="font-bold text-dark-primary">{course.student_count}</span>
            </div>

            <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2 text-light-text">
                    <Clock size={16} />
                    <span>Credits</span>
                </div>
                <span className="font-bold text-dark-primary">{course.credits}</span>
            </div>

            <div className="pt-4 border-t border-light-secondary/50">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold text-light-text uppercase tracking-wider">Syllabus Progress</span>
                    <span className="text-xs font-bold text-dark-primary">{course.progress}%</span>
                </div>
                <div className="w-full bg-light-bg h-2 rounded-full overflow-hidden">
                    <div
                        className="bg-dark-highlight h-full transition-all duration-1000"
                        style={{ width: `${course.progress}%` }}
                    ></div>
                </div>
            </div>
        </div>

        <button className="mt-6 w-full py-3 rounded-xl bg-light-bg text-dark-primary font-bold text-sm hover:bg-dark-highlight transition-all">
            Open Course
        </button>
    </div>
);

const Courses = () => {
    const dummyCourses = [
        { id: 1, course_name: 'Data Structures', course_code: 'CS-302', credits: 4, student_count: 45, progress: 75, color: 'bg-blue-600' },
        { id: 2, course_name: 'Design of Algorithms', course_code: 'CS-401', credits: 4, student_count: 42, progress: 40, color: 'bg-teal-600' },
        { id: 3, course_name: 'Database Systems', course_code: 'CS-205', credits: 3, student_count: 50, progress: 90, color: 'bg-indigo-600' },
        { id: 4, course_name: 'Operating Systems', course_code: 'CS-305', credits: 4, student_count: 38, progress: 15, color: 'bg-emerald-600' },
    ];

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-dark-primary">Courses</h1>
                    <p className="text-light-text mt-1">Manage your active semesters and curriculum.</p>
                </div>
                <button className="bg-dark-primary text-white px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-dark-secondary transition-all shadow-lg shadow-dark-primary/20">
                    <Plus size={20} />
                    Add Course
                </button>
            </div>

            <div className="flex gap-4 items-center bg-white p-2 rounded-2xl border border-light-secondary/50 max-w-md">
                <div className="flex-1 flex items-center gap-2 px-4">
                    <Search size={18} className="text-light-text/50" />
                    <input
                        type="text"
                        placeholder="Search courses..."
                        className="bg-transparent border-none outline-none text-sm w-full py-2"
                    />
                </div>
                <div className="h-6 w-px bg-light-secondary"></div>
                <select className="bg-transparent border-none outline-none text-sm font-semibold text-dark-primary px-4 cursor-pointer">
                    <option>Fall 2025</option>
                    <option>Spring 2025</option>
                </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {dummyCourses.map(course => (
                    <CourseCard key={course.id} course={course} />
                ))}
            </div>
        </div>
    );
};

export default Courses;
