import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.karix.one',
  appName: 'ONE',
  webDir: 'build',
   server: {
    // Emulator: 10.0.2.2 is the emulator's alias for your PC
    // Real phone: use your PC's LAN IP instead, e.g. http://192.168.1.25:5173
    url: 'http://10.0.2.2:5173',
    cleartext: true
  }
};

export default config;
