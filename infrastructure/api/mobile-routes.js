const express = require('express');
const router = express.Router();

// Mobile dashboard summary
router.get('/dashboard', async (req, res) => {
  try {
    const { userId } = req.user;
    
    const summary = await getDashboardSummary(userId);
    
    res.json({
      success: true,
      data: {
        totalAudits: summary.totalAudits,
        averageScore: summary.averageScore,
        recentAudits: summary.recentAudits.map(audit => ({
          id: audit.id,
          url: audit.url,
          score: audit.overallScore,
          grade: audit.grade,
          completedAt: audit.completedAt,
          alerts: audit.criticalIssues.length
        })),
        alerts: summary.criticalAlerts,
        trends: summary.scoreTrends
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Real-time audit status
router.get('/audit/:id/status', async (req, res) => {
  try {
    const { id } = req.params;
    const status = await getAuditStatus(id);
    
    res.json({
      success: true,
      data: {
        id,
        status: status.status,
        progress: status.progress,
        currentStep: status.currentStep,
        estimatedCompletion: status.estimatedCompletion,
        results: status.partialResults
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Mobile-optimized audit results
router.get('/audit/:id/mobile', async (req, res) => {
  try {
    const { id } = req.params;
    const audit = await getAuditResults(id);
    
    // Mobile-optimized response
    res.json({
      success: true,
      data: {
        id: audit.id,
        url: audit.url,
        score: audit.overallScore,
        grade: audit.grade,
        completedAt: audit.completedAt,
        summary: {
          technical: {
            score: audit.technicalScore,
            grade: getGrade(audit.technicalScore),
            topIssues: audit.technicalIssues.slice(0, 3)
          },
          content: {
            score: audit.contentScore,
            grade: getGrade(audit.contentScore),
            topIssues: audit.contentIssues.slice(0, 3)
          },
          ai: {
            score: audit.aiScore,
            grade: getGrade(audit.aiScore),
            topIssues: audit.aiIssues.slice(0, 3)
          }
        },
        quickActions: generateQuickActions(audit),
        shareUrl: generateShareUrl(audit.id)
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Push notification registration
router.post('/notifications/register', async (req, res) => {
  try {
    const { deviceToken, platform } = req.body;
    const { userId } = req.user;
    
    await registerDevice(userId, deviceToken, platform);
    
    res.json({ success: true, message: 'Device registered for notifications' });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Quick audit trigger
router.post('/audit/quick', async (req, res) => {
  try {
    const { url } = req.body;
    const { userId } = req.user;
    
    const auditId = await startQuickAudit(userId, url);
    
    res.json({
      success: true,
      data: {
        auditId,
        status: 'started',
        estimatedCompletion: new Date(Date.now() + 5 * 60 * 1000) // 5 minutes
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

function getGrade(score) {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
}

function generateQuickActions(audit) {
  const actions = [];
  
  if (audit.technicalScore < 70) {
    actions.push({
      type: 'technical',
      title: 'Fix Technical Issues',
      priority: 'high',
      count: audit.technicalIssues.length
    });
  }
  
  if (audit.aiScore < 80) {
    actions.push({
      type: 'ai',
      title: 'Improve AI Visibility',
      priority: 'medium',
      count: audit.aiIssues.length
    });
  }
  
  return actions;
}

module.exports = router;