
// data/models/alert.model.js
/**
 * Alert model for unified alert format
 */
class Alert {
  constructor(id, timestamp, description, level, source, type, details) {
    this.id = id;
    this.timestamp = timestamp;
    this.description = description;
    this.level = level;
    this.source = source;
    this.type = type;
    this.details = details;
  }

  // Create from WAZUH alert
  static fromWazuh(wazuhAlert) {
    return new Alert(
      wazuhAlert.id,
      wazuhAlert.timestamp,
      wazuhAlert.rule?.description || 'Unknown alert',
      wazuhAlert.rule?.level || 0,
      'wazuh',
      this._determineWazuhAlertType(wazuhAlert),
      wazuhAlert
    );
  }

  // Create from keystroke alert
  static fromKeystroke(keystrokeAlert) {
    return new Alert(
      keystrokeAlert.id,
      keystrokeAlert.timestamp,
      `Keystroke anomaly detected with ${keystrokeAlert.confidence.toFixed(2)}% confidence`,
      keystrokeAlert.confidence > 90 ? 15 : (keystrokeAlert.confidence > 75 ? 10 : 5),
      'keystroke',
      `keystroke_${keystrokeAlert.model_type}`,
      keystrokeAlert
    );
  }

  // Create from anomaly alert
  static fromAnomaly(anomalyAlert) {
    return new Alert(
      anomalyAlert.id,
      anomalyAlert.timestamp,
      anomalyAlert.details?.description || 'Anomaly detected',
      anomalyAlert.score >= 90 ? 15 : (anomalyAlert.score >= 75 ? 10 : 5),
      'anomaly',
      'opensearch_anomaly',
      anomalyAlert
    );
  }

  // Determine WAZUH alert type
  static _determineWazuhAlertType(alert) {
    if (alert.rule?.groups?.includes('syscheck')) {
      return 'fim';
    } else if (alert.rule?.groups?.includes('vulnerability-detector')) {
      return 'vulnerability';
    } else if (alert.rule?.groups?.includes('virustotal') || 
               alert.rule?.groups?.includes('rootkit')) {
      return 'malware';
    } else {
      return 'other';
    }
  }
}

module.exports = Alert;