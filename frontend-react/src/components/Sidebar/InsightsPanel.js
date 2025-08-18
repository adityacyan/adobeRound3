import React, { useState, useEffect } from 'react';
import { Brain, TrendingUp, AlertTriangle, BookOpen, Lightbulb, RefreshCw } from 'lucide-react';
import { getDocumentContent, generateInsights } from '../../services/api';

const InsightsPanel = ({
    sessionId,
    activeDocumentId,
    insights,
    setInsights,
    loading
}) => {
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState(null);
    const [cache, setCache] = useState(new Map());

    useEffect(() => {
        if (activeDocumentId && sessionId) {
            loadInsights();
        }
    }, [activeDocumentId, sessionId]);

    const loadInsights = async () => {
        if (!activeDocumentId || !sessionId) return;

        // Check cache first
        const cacheKey = `${sessionId}_${activeDocumentId}`;
        if (cache.has(cacheKey)) {
            setInsights(cache.get(cacheKey));
            return;
        }

        setGenerating(true);
        setError(null);

        try {
            // Get document content
            const contentData = await getDocumentContent(sessionId, activeDocumentId);

            if (!contentData.content) {
                setError('No content available for this document');
                return;
            }

            // Generate insights
            const insightsData = await generateInsights(contentData.content);

            if (insightsData.success) {
                const newInsights = insightsData.insights;
                setInsights(newInsights);

                // Cache the results
                setCache(prev => new Map(prev.set(cacheKey, newInsights)));
            } else {
                setError(insightsData.error || 'Failed to generate insights');
            }
        } catch (error) {
            console.error('Error loading insights:', error);
            setError('Failed to load insights. Please try again.');
        } finally {
            setGenerating(false);
        }
    };

    const handleRefresh = () => {
        // Clear cache for current document
        const cacheKey = `${sessionId}_${activeDocumentId}`;
        setCache(prev => {
            const newCache = new Map(prev);
            newCache.delete(cacheKey);
            return newCache;
        });

        setInsights(null);
        loadInsights();
    };

    const InsightSection = ({ title, items, icon: Icon, color, emptyMessage }) => (
        <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                    <Icon className={`h-5 w-5 mr-2 ${color}`} />
                    <h4 className="font-medium text-gray-700">{title}</h4>
                </div>
                <span className="text-xs text-gray-500">{items?.length || 0}</span>
            </div>

            <div className="space-y-2">
                {items && items.length > 0 ? (
                    items.map((item, index) => (
                        <div key={index} className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 leading-relaxed">
                            • {item}
                        </div>
                    ))
                ) : (
                    <div className="p-3 bg-gray-50 rounded-lg text-sm text-gray-500 italic">
                        {emptyMessage}
                    </div>
                )}
            </div>
        </div>
    );

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                    <Brain className="h-5 w-5 mr-2 text-blue-600" />
                    AI Insights
                </h3>
                <button
                    onClick={handleRefresh}
                    disabled={generating}
                    className={`
            p-2 rounded-lg transition-colors text-sm
            ${generating
                            ? 'text-gray-400 cursor-not-allowed'
                            : 'text-gray-600 hover:bg-gray-100'
                        }
          `}
                    title="Refresh insights"
                >
                    <RefreshCw className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {!activeDocumentId ? (
                <div className="text-center py-8">
                    <Brain className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Select a document to view AI insights</p>
                </div>
            ) : generating ? (
                <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-gray-600 font-medium">Generating AI insights...</p>
                    <p className="text-sm text-gray-500 mt-1">This may take a few seconds</p>
                </div>
            ) : error ? (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-center">
                        <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                        <span className="text-red-700 text-sm">{error}</span>
                    </div>
                    <button
                        onClick={handleRefresh}
                        className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
                    >
                        Try again
                    </button>
                </div>
            ) : insights ? (
                <div className="space-y-1">
                    <InsightSection
                        title="Key Takeaways"
                        items={insights.takeaways}
                        icon={TrendingUp}
                        color="text-green-600"
                        emptyMessage="No key takeaways found"
                    />

                    <InsightSection
                        title="Contradictions"
                        items={insights.contradictions}
                        icon={AlertTriangle}
                        color="text-red-600"
                        emptyMessage="No contradictions found"
                    />

                    <InsightSection
                        title="Examples"
                        items={insights.examples}
                        icon={BookOpen}
                        color="text-blue-600"
                        emptyMessage="No examples found"
                    />

                    <InsightSection
                        title="Did You Know?"
                        items={insights.did_you_know}
                        icon={Lightbulb}
                        color="text-yellow-600"
                        emptyMessage="No interesting facts found"
                    />

                    {insights.processing_time && (
                        <div className="text-xs text-gray-500 text-center mt-4 pt-4 border-t">
                            Generated in {insights.processing_time.toFixed(2)}s
                        </div>
                    )}
                </div>
            ) : (
                <div className="text-center py-8">
                    <Brain className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Click to generate insights for this document</p>
                    <button
                        onClick={loadInsights}
                        className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                    >
                        Generate Insights
                    </button>
                </div>
            )}
        </div>
    );
};

export default InsightsPanel;
