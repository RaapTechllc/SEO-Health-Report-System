import React from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/Tabs';
import { Skeleton } from './ui/Skeleton';
import ScoreGauge from './ScoreGauge';

export default function ComponentTest() {
  return (
    <div className="p-8 space-y-8">
      <h2 className="text-2xl font-bold">Component Test</h2>
      
      {/* Score Gauge Test */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Score Gauge (Recharts + Animation)</h3>
        <div className="flex gap-8">
          <ScoreGauge score={85} size="lg" />
          <ScoreGauge score={65} size="sm" />
        </div>
      </div>

      {/* Tabs Test */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Tabs Component</h3>
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Technical</TabsTrigger>
            <TabsTrigger value="tab2">Content</TabsTrigger>
            <TabsTrigger value="tab3">AI Visibility</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">
            <p>Technical audit content here...</p>
          </TabsContent>
          <TabsContent value="tab2">
            <p>Content audit content here...</p>
          </TabsContent>
          <TabsContent value="tab3">
            <p>AI visibility audit content here...</p>
          </TabsContent>
        </Tabs>
      </div>

      {/* Skeleton Test */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Skeleton Loading</h3>
        <div className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    </div>
  );
}