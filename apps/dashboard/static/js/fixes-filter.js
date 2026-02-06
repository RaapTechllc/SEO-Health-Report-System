/**
 * Fixes List Filter - Priority-based filtering for the fixes list component
 */
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const fixesList = document.getElementById('fixes-list');
    const noFixesMessage = document.getElementById('no-fixes-message');
    
    if (!filterButtons.length || !fixesList) return;
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const priority = this.dataset.priority;
            
            // Update active state on buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter fix items
            const fixItems = fixesList.querySelectorAll('.fix-item');
            let visibleCount = 0;
            
            fixItems.forEach(item => {
                if (priority === 'all' || item.dataset.priority === priority) {
                    item.style.display = '';
                    visibleCount++;
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Show/hide "no matches" message
            if (noFixesMessage) {
                if (visibleCount === 0 && fixItems.length > 0) {
                    noFixesMessage.classList.remove('hidden');
                } else {
                    noFixesMessage.classList.add('hidden');
                }
            }
        });
    });
});
