const WebSocket = require('ws');
const Redis = require('redis');

class RealTimeService {
  constructor() {
    this.wss = new WebSocket.Server({ port: 8080 });
    this.redis = Redis.createClient({ url: process.env.REDIS_URL });
    this.clients = new Map();
    
    this.setupWebSocketServer();
    this.setupRedisSubscriber();
  }

  setupWebSocketServer() {
    this.wss.on('connection', (ws, req) => {
      const clientId = this.generateClientId();
      this.clients.set(clientId, { ws, subscriptions: new Set() });

      ws.on('message', (message) => {
        try {
          const data = JSON.parse(message);
          this.handleClientMessage(clientId, data);
        } catch (error) {
          console.error('Invalid message format:', error);
        }
      });

      ws.on('close', () => {
        this.clients.delete(clientId);
      });

      // Send connection confirmation
      ws.send(JSON.stringify({
        type: 'connected',
        clientId,
        timestamp: new Date().toISOString()
      }));
    });
  }

  setupRedisSubscriber() {
    this.redis.subscribe('audit:progress', 'audit:complete', 'system:alerts');
    
    this.redis.on('message', (channel, message) => {
      try {
        const data = JSON.parse(message);
        this.broadcastUpdate(channel, data);
      } catch (error) {
        console.error('Redis message parse error:', error);
      }
    });
  }

  handleClientMessage(clientId, data) {
    const client = this.clients.get(clientId);
    if (!client) return;

    switch (data.type) {
      case 'subscribe':
        client.subscriptions.add(data.channel);
        break;
      case 'unsubscribe':
        client.subscriptions.delete(data.channel);
        break;
      case 'ping':
        client.ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
        break;
    }
  }

  broadcastUpdate(channel, data) {
    const message = JSON.stringify({
      type: 'update',
      channel,
      data,
      timestamp: new Date().toISOString()
    });

    this.clients.forEach((client) => {
      if (client.subscriptions.has(channel) && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(message);
      }
    });
  }

  // Publish audit progress updates
  publishAuditProgress(auditId, progress) {
    this.redis.publish('audit:progress', JSON.stringify({
      auditId,
      progress,
      timestamp: new Date().toISOString()
    }));
  }

  // Publish audit completion
  publishAuditComplete(auditId, results) {
    this.redis.publish('audit:complete', JSON.stringify({
      auditId,
      results,
      timestamp: new Date().toISOString()
    }));
  }

  // Publish system alerts
  publishAlert(level, message, details = {}) {
    this.redis.publish('system:alerts', JSON.stringify({
      level,
      message,
      details,
      timestamp: new Date().toISOString()
    }));
  }

  generateClientId() {
    return Math.random().toString(36).substring(2, 15);
  }
}

module.exports = RealTimeService;