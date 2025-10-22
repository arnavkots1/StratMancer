import type { Metadata } from 'next'
import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Settings, Palette, Bell, Shield, BarChart3, Download, Trash2 } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Settings - StratMancer',
  description: 'Manage your StratMancer preferences and settings',
}

export default function SettingsPage() {
  return (
    <Container className="py-16">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold gradient-text mb-4">Settings</h1>
          <p className="text-muted-foreground text-lg">
            Customize your StratMancer experience
          </p>
        </div>

        <div className="space-y-8">
          {/* Appearance Settings */}
          <Card className="p-6">
            <div className="flex items-center mb-6">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 mr-4">
                <Palette className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Appearance</h2>
                <p className="text-muted-foreground text-sm">Customize the look and feel of StratMancer</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="animations" className="text-base font-medium">Animations</Label>
                  <p className="text-sm text-muted-foreground">Enable or disable UI animations</p>
                </div>
                <Switch id="animations" defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="reduced-motion" className="text-base font-medium">Reduced Motion</Label>
                  <p className="text-sm text-muted-foreground">Minimize motion for accessibility</p>
                </div>
                <Switch id="reduced-motion" />
              </div>
            </div>
          </Card>

          {/* Draft Preferences */}
          <Card className="p-6">
            <div className="flex items-center mb-6">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-secondary/10 border border-secondary/20 mr-4">
                <Settings className="w-5 h-5 text-secondary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Draft Preferences</h2>
                <p className="text-sm text-muted-foreground">Configure your default draft settings</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="default-elo" className="text-base font-medium">Default ELO</Label>
                  <p className="text-sm text-muted-foreground">Your primary skill level for analysis</p>
                </div>
                <Select defaultValue="mid">
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low (Iron-Gold)</SelectItem>
                    <SelectItem value="mid">Mid (Platinum-Diamond)</SelectItem>
                    <SelectItem value="high">High (Master+)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="auto-save" className="text-base font-medium">Auto-save Drafts</Label>
                  <p className="text-sm text-muted-foreground">Automatically save draft progress</p>
                </div>
                <Switch id="auto-save" defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="show-tips" className="text-base font-medium">Show Tips</Label>
                  <p className="text-sm text-muted-foreground">Display helpful tips and hints</p>
                </div>
                <Switch id="show-tips" defaultChecked />
              </div>
            </div>
          </Card>

          {/* Notifications */}
          <Card className="p-6">
            <div className="flex items-center mb-6">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 mr-4">
                <Bell className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Notifications</h2>
                <p className="text-sm text-muted-foreground">Manage your notification preferences</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="browser-notifications" className="text-base font-medium">Browser Notifications</Label>
                  <p className="text-sm text-muted-foreground">Allow browser notifications</p>
                </div>
                <Switch id="browser-notifications" />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="update-notifications" className="text-base font-medium">Update Notifications</Label>
                  <p className="text-sm text-muted-foreground">Get notified about new features</p>
                </div>
                <Switch id="update-notifications" defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="maintenance-notifications" className="text-base font-medium">Maintenance Alerts</Label>
                  <p className="text-sm text-muted-foreground">Notify about scheduled maintenance</p>
                </div>
                <Switch id="maintenance-notifications" defaultChecked />
              </div>
            </div>
          </Card>

          {/* Privacy & Data */}
          <Card className="p-6">
            <div className="flex items-center mb-6">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-green-500/10 border border-green-500/20 mr-4">
                <Shield className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Privacy & Data</h2>
                <p className="text-sm text-muted-foreground">Control your data and privacy settings</p>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="analytics" className="text-base font-medium">Analytics Tracking</Label>
                  <p className="text-sm text-muted-foreground">Help us improve by sharing usage data</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch id="analytics" defaultChecked />
                  <Badge variant="secondary" className="text-xs">Recommended</Badge>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="performance-tracking" className="text-base font-medium">Performance Tracking</Label>
                  <p className="text-sm text-muted-foreground">Monitor app performance and errors</p>
                </div>
                <Switch id="performance-tracking" defaultChecked />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="crash-reporting" className="text-base font-medium">Crash Reporting</Label>
                  <p className="text-sm text-muted-foreground">Automatically report crashes and errors</p>
                </div>
                <Switch id="crash-reporting" defaultChecked />
              </div>
            </div>
          </Card>

          {/* Data Management */}
          <Card className="p-6">
            <div className="flex items-center mb-6">
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 mr-4">
                <BarChart3 className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Data Management</h2>
                <p className="text-sm text-muted-foreground">Manage your stored data and preferences</p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium">Export Data</h3>
                  <p className="text-sm text-muted-foreground">Download your settings and preferences</p>
                </div>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium">Clear Cache</h3>
                  <p className="text-sm text-muted-foreground">Clear stored cache and temporary data</p>
                </div>
                <Button variant="outline" size="sm">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Clear
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 border border-destructive/20 rounded-lg bg-destructive/5">
                <div>
                  <h3 className="font-medium text-destructive">Reset All Settings</h3>
                  <p className="text-sm text-muted-foreground">Reset all preferences to default values</p>
                </div>
                <Button variant="destructive" size="sm">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Reset
                </Button>
              </div>
            </div>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <Button size="lg" className="px-8">
              Save Settings
            </Button>
          </div>
        </div>
      </div>
    </Container>
  )
}
