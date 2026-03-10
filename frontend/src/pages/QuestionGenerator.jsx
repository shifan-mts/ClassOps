import React, { useState } from 'react';
import { FileText, Wand2, Settings, Download, ArrowRight, CheckCircle2 } from 'lucide-react';

const QuestionGenerator = () => {
    const [step, setStep] = useState(1);
    const [formData, setFormData] = useState({
        subject: 'Data Structures',
        units: ['Trees', 'Graphs'],
        difficulty: 'medium',
        format: 'standard',
        blooms: {
            knowledge: 20,
            application: 40,
            analysis: 40
        }
    });

    const handleBloomChange = (key, val) => {
        setFormData(prev => ({
            ...prev,
            blooms: { ...prev.blooms, [key]: parseInt(val) }
        }));
    };

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-700">
            <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold text-dark-primary">Question Paper Generator</h1>
                <p className="text-light-text max-w-2xl mx-auto">Generate balanced question papers using AI based on Bloom's Taxonomy and course curriculum.</p>
            </div>

            <div className="flex justify-center mb-8">
                <div className="flex items-center gap-4 bg-white p-2 rounded-2xl border border-light-secondary/50">
                    {[1, 2, 3].map((s) => (
                        <div key={s} className="flex items-center gap-2 px-4 py-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${s === step ? 'bg-dark-primary text-white shadow-lg shadow-dark-primary/20 scale-110' :
                                    s < step ? 'bg-dark-highlight text-dark-primary' : 'bg-light-bg text-light-text'
                                }`}>
                                {s < step ? <CheckCircle2 size={16} /> : s}
                            </div>
                            <span className={`text-sm font-bold ${s === step ? 'text-dark-primary' : 'text-light-text'}`}>
                                {s === 1 ? 'Configure' : s === 2 ? 'Bloom\'s Distribution' : 'Generate'}
                            </span>
                            {s < 3 && <ArrowRight size={14} className="text-light-secondary ml-2" />}
                        </div>
                    ))}
                </div>
            </div>

            <div className="bg-white rounded-[40px] border border-light-secondary/50 shadow-xl shadow-dark-primary/5 overflow-hidden ring-1 ring-light-secondary/20">
                <div className="p-12">
                    {step === 1 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-dark-primary uppercase tracking-wider flex items-center gap-2">
                                        <Settings size={16} className="text-dark-accent" />
                                        Subject & Semester
                                    </label>
                                    <select className="w-full bg-light-bg px-6 py-4 rounded-2xl border-none outline-none font-semibold text-dark-primary focus:ring-2 focus:ring-dark-accent/20 transition-all">
                                        <option>Data Structures (CS-302)</option>
                                        <option>Algorithms (CS-401)</option>
                                    </select>
                                </div>

                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-dark-primary uppercase tracking-wider">Units to Include</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        {['Arrays', 'Linked Lists', 'Stacks', 'Queues', 'Trees', 'Graphs'].map(unit => (
                                            <label key={unit} className="flex items-center gap-3 bg-light-bg px-4 py-3 rounded-xl cursor-pointer hover:bg-dark-highlight/30 transition-all border border-transparent has-[:checked]:border-dark-accent has-[:checked]:bg-dark-highlight/20 group">
                                                <input type="checkbox" className="hidden" defaultChecked={formData.units.includes(unit)} />
                                                <span className="w-4 h-4 rounded border-2 border-light-secondary flex items-center justify-center group-has-[:checked]:border-dark-accent group-has-[:checked]:bg-dark-accent transition-all">
                                                    <CheckCircle2 size={12} className="text-white opacity-0 group-has-[:checked]:opacity-100" />
                                                </span>
                                                <span className="text-sm font-semibold text-dark-primary">{unit}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-dark-primary uppercase tracking-wider">Difficulty Level</label>
                                    <div className="flex gap-4">
                                        {['Easy', 'Medium', 'Hard'].map(level => (
                                            <button
                                                key={level}
                                                className={`flex-1 py-4 rounded-2xl font-bold transition-all ${formData.difficulty === level.toLowerCase()
                                                        ? 'bg-dark-primary text-white shadow-lg shadow-dark-primary/20'
                                                        : 'bg-light-bg text-light-text hover:bg-light-secondary'
                                                    }`}
                                            >
                                                {level}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <label className="text-sm font-bold text-dark-primary uppercase tracking-wider">Output Format</label>
                                    <div className="space-y-3">
                                        {['Standard (A, B, C Sections)', 'Quiz Style (MCQs)', 'Case Study Based'].map(fmt => (
                                            <div key={fmt} className="flex items-center gap-4 p-4 rounded-2xl border border-light-secondary hover:border-dark-accent transition-all cursor-pointer group">
                                                <div className="w-10 h-10 rounded-xl bg-light-bg flex items-center justify-center text-light-text group-hover:text-dark-primary transition-all">
                                                    <FileText size={18} />
                                                </div>
                                                <span className="font-bold text-dark-primary text-sm">{fmt}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-12">
                            <div className="text-center max-w-xl mx-auto">
                                <h3 className="text-2xl font-bold text-dark-primary">Bloom's Taxonomy Balance</h3>
                                <p className="text-light-text mt-2">Adjust the percentage of questions for each cognitive level.</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                {['knowledge', 'application', 'analysis'].map(level => (
                                    <div key={level} className="bg-light-bg p-8 rounded-3xl space-y-6 text-center">
                                        <div className="text-4xl font-black text-dark-accent">{formData.blooms[level]}%</div>
                                        <label className="text-sm font-bold text-dark-primary uppercase tracking-widest">{level}</label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={formData.blooms[level]}
                                            onChange={(e) => handleBloomChange(level, e.target.value)}
                                            className="w-full accent-dark-accent"
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="bg-dark-highlight/20 p-6 rounded-2xl border border-dark-highlight flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-full bg-dark-highlight flex items-center justify-center text-dark-primary font-bold">
                                        {Object.values(formData.blooms).reduce((a, b) => a + b, 0)}%
                                    </div>
                                    <p className="text-sm font-bold text-dark-primary">Total Distribution</p>
                                </div>
                                {Object.values(formData.blooms).reduce((a, b) => a + b, 0) !== 100 && (
                                    <p className="text-sm font-bold text-red-500">Distribution must equal 100%</p>
                                )}
                            </div>
                        </div>
                    )}

                    <div className="mt-12 flex justify-between pt-8 border-t border-light-secondary/50">
                        {step > 1 && (
                            <button
                                onClick={() => setStep(step - 1)}
                                className="px-8 py-4 rounded-xl font-bold text-dark-primary hover:bg-light-bg transition-all"
                            >
                                Back
                            </button>
                        )}
                        <div className="flex-1"></div>
                        <button
                            onClick={() => step < 3 ? setStep(step + 1) : null}
                            className="px-10 py-4 bg-dark-primary text-white rounded-2xl font-bold hover:bg-dark-secondary transition-all flex items-center gap-2 shadow-xl shadow-dark-primary/10 group"
                        >
                            {step === 3 ? 'Generate Paper' : 'Continue'}
                            <Wand2 size={20} className="group-hover:rotate-12 transition-transform" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default QuestionGenerator;
