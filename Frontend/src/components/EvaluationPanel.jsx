import React, { useState, useEffect } from 'react';

const EvaluationPanel = ({ API_BASE, courseId }) => {
  const [evaluations, setEvaluations] = useState([]);
  const [averages, setAverages] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const evalQuestions = [
    { id: 'Q1', text: 'The course objectives were clearly explained.' },
    { id: 'Q2', text: 'The syllabus content was relevant to the programme.' },
    { id: 'Q3', text: 'The course content helped in improving subject knowledge.' },
    { id: 'Q4', text: 'The prescribed textbook / reference materials were useful.' },
    { id: 'Q5', text: 'The course improved my understanding of the subject and it helped in achieving learning outcomes.' },
    { id: 'Q6', text: 'Internal assessments reflected the taught syllabus.' },
    { id: 'Q7', text: 'Assignments / tests supported learning effectively.' },
    { id: 'Q8', text: 'Evaluation methods were fair and transparent.' },
    { id: 'Q9', text: 'The course improved problem-solving / analytical ability.' },
    { id: 'Q10', text: 'The course helped in achieving the intended learning outcomes.' },
  ];

  useEffect(() => {
    if (!courseId) return;

    let isMounted = true;

    const fetchEvaluations = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/courses/${courseId}/evaluations`, {
          credentials: 'include'
        });
        const data = await response.json();
        
        if (response.ok) {
          if (isMounted) {
            setEvaluations(data.evaluations || []);
            setAverages(data.averages || {});
            setError('');
          }
        } else {
          if (isMounted) setError(data.error || 'Failed to fetch evaluations.');
        }
      } catch (err) {
        if (isMounted) setError('Error fetching evaluations.');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    setLoading(true);
    fetchEvaluations();
    const interval = setInterval(fetchEvaluations, 5000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [courseId, API_BASE]);

  const handleDownload = () => {
    window.open(`${API_BASE}/api/courses/${courseId}/evaluations/download`, '_blank');
  };

  if (!courseId) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="placeholder">Please select a classroom from the Overview tab to view its evaluations.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3>Course Evaluations</h3>
          <p>Review student feedback and ratings for this course.</p>
        </div>
        {evaluations.length > 0 && (
          <button onClick={handleDownload} className="primary" style={{ padding: '8px 16px', borderRadius: '8px' }}>
            Download CSV Report
          </button>
        )}
      </div>

      <div className="card-body">
        {loading ? (
          <div className="placeholder">Loading evaluation data...</div>
        ) : error ? (
          <div className="status warn">Error: {error}</div>
        ) : evaluations.length === 0 ? (
          <div className="placeholder">No evaluations have been submitted for this course yet.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
            
            <div style={{ padding: '24px', background: '#f8fafc', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
              <h4 style={{ margin: '0 0 16px', fontSize: '1.2rem', color: '#0f172a' }}>Marks Graph (Averages out of 5)</h4>
              <p style={{ margin: '0 0 24px', fontSize: '0.9rem', color: '#64748b' }}>Based on {evaluations.length} student submissions.</p>
              
              <div style={{ display: 'grid', gap: '20px' }}>
                {evalQuestions.map(q => {
                  const avg = averages[q.id] || 0;
                  const percentage = (avg / 5) * 100;
                  
                  // Color coding based on average
                  let barColor = '#10b981'; // Green for high
                  if (avg < 3) barColor = '#ef4444'; // Red for low
                  else if (avg < 4) barColor = '#f59e0b'; // Yellow for medium

                  return (
                    <div key={q.id} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#334155', fontWeight: 600 }}>
                        <span>{q.id}: {q.text}</span>
                        <span style={{ fontWeight: 700, color: barColor }}>{avg.toFixed(2)}</span>
                      </div>
                      <div style={{ width: '100%', height: '12px', background: '#e2e8f0', borderRadius: '6px', overflow: 'hidden' }}>
                        <div style={{ 
                          width: `${percentage}%`, 
                          height: '100%', 
                          background: barColor,
                          borderRadius: '6px',
                          transition: 'width 1s ease-out'
                        }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div style={{ padding: '24px', background: '#fff', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
              <h4 style={{ margin: '0 0 16px', fontSize: '1.2rem', color: '#0f172a' }}>Recent Submissions</h4>
              <div style={{ display: 'grid', gap: '12px' }}>
                {evaluations.slice(0, 5).map((ev, idx) => (
                  <div key={idx} style={{ padding: '12px', background: '#f1f5f9', borderRadius: '8px', fontSize: '0.9rem', color: '#475569', display: 'flex', justifyContent: 'space-between' }}>
                    <span>{ev.student_email || 'Anonymous Student'}</span>
                    <span>{new Date(ev.timestamp).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationPanel;
