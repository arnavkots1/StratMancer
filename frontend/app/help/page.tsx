/* eslint-disable react/no-unescaped-entities */
"use client"

import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { HelpCircle, Search, MessageSquare, BookOpen, Video, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

const faqCategories = [
  {
    id: 'getting-started',
    title: 'Getting Started',
    icon: BookOpen,
    color: 'text-blue-500',
    bgColor: 'bg-blue-100',
    questions: [
      {
        question: 'How do I use the Draft Analyzer?',
        answer: 'The Draft Analyzer helps you make better champion picks during the draft phase. Simply select champions as they\'re picked or banned, and our AI will provide real-time win probability predictions and recommendations for your next pick.'
      },
      {
        question: 'What ELO levels are supported?',
        answer: 'RiftAI supports three ELO tiers: Low (Iron-Gold), Mid (Platinum-Diamond), and High (Master+). Each tier has its own trained model to provide accurate predictions for your skill level.'
      },
      {
        question: 'How accurate are the predictions?',
        answer: 'Our models achieve high accuracy rates across all ELO tiers. The exact accuracy varies by tier and meta changes, but we continuously update our models with the latest match data to maintain optimal performance.'
      }
    ]
  },
  {
    id: 'features',
    title: 'Features',
    icon: FileText,
    color: 'text-green-500',
    bgColor: 'bg-green-100',
    questions: [
      {
        question: 'What is the Meta Tracker?',
        answer: 'The Meta Tracker shows current champion popularity, win rates, and tier lists for each ELO bracket. It helps you understand the current meta and make informed decisions about champion picks and bans.'
      },
      {
        question: 'How does the AI reasoning work?',
        answer: 'Our AI analyzes team compositions, champion synergies, counter-picks, and meta trends to provide detailed explanations for its recommendations. The reasoning appears as a typewriter animation in the recommendations panel.'
      },
      {
        question: 'Can I save my draft analysis?',
        answer: 'Currently, draft analysis is session-based. We\'re working on adding draft history and saving functionality in future updates.'
      }
    ]
  },
  {
    id: 'technical',
    title: 'Technical',
    icon: HelpCircle,
    color: 'text-purple-500',
    bgColor: 'bg-purple-100',
    questions: [
      {
        question: 'Why is my model confidence low?',
        answer: 'Model confidence can be low due to several factors: limited training data for certain champion combinations, recent meta shifts, or unusual draft compositions. We continuously improve our models to increase confidence levels.'
      },
      {
        question: 'The website is loading slowly. What should I do?',
        answer: 'Try refreshing the page, clearing your browser cache, or checking your internet connection. If issues persist, please contact our support team with details about your browser and device.'
      },
      {
        question: 'Are there any browser requirements?',
        answer: 'RiftAI works best on modern browsers (Chrome, Firefox, Safari, Edge) with JavaScript enabled. We recommend using the latest version of your preferred browser for the best experience.'
      }
    ]
  },
  {
    id: 'account',
    title: 'Account & Privacy',
    icon: MessageSquare,
    color: 'text-orange-500',
    bgColor: 'bg-orange-100',
    questions: [
      {
        question: 'Do I need an account to use RiftAI?',
        answer: 'No account is required! RiftAI is free to use without registration. All your preferences are stored locally in your browser.'
      },
      {
        question: 'How is my data protected?',
        answer: 'We take privacy seriously. Draft data is processed locally and not stored permanently. We only collect minimal analytics data to improve our service. See our Privacy Policy for full details.'
      },
      {
        question: 'Can I delete my data?',
        answer: 'Yes! You can clear all your local data through the Settings page, or contact us if you have any concerns about data deletion.'
      }
    ]
  }
]

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Card className="p-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left"
      >
        <h3 className="font-medium text-foreground">{question}</h3>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-5 h-5 text-muted-foreground" />
        )}
      </button>
      {isOpen && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-muted-foreground leading-relaxed">{answer}</p>
        </div>
      )}
    </Card>
  )
}

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const filteredCategories = faqCategories.filter(category => {
    if (selectedCategory && category.id !== selectedCategory) return false
    if (!searchQuery) return true
    
    const searchLower = searchQuery.toLowerCase()
    return category.title.toLowerCase().includes(searchLower) ||
           category.questions.some(q => 
             q.question.toLowerCase().includes(searchLower) ||
             q.answer.toLowerCase().includes(searchLower)
           )
  })

  return (
    <Container className="py-16">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold gradient-text mb-6">RiftAI Help Center</h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            Find answers to common questions, learn how to use RiftAI effectively, 
            and get the support you need.
          </p>
        </div>

        {/* Search Bar */}
        <Card className="p-6 mb-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
            <Input
              placeholder="Search for help articles, FAQs, or guides..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </Card>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <Card className="p-6 text-center hover:shadow-lg transition-shadow">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 mb-4">
              <MessageSquare className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Contact Support</h3>
            <p className="text-muted-foreground text-sm mb-4">
              Can't find what you're looking for? Our support team is here to help.
            </p>
            <Button variant="outline" className="w-full" disabled>
              Coming Soon
            </Button>
          </Card>

          <Card className="p-6 text-center hover:shadow-lg transition-shadow">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-secondary/10 border border-secondary/20 mb-4">
              <Video className="w-6 h-6 text-secondary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Video Tutorials</h3>
            <p className="text-muted-foreground text-sm mb-4">
              Watch step-by-step guides to master RiftAI features.
            </p>
            <Button variant="outline" className="w-full" disabled>
              Coming Soon
            </Button>
          </Card>

          <Card className="p-6 text-center hover:shadow-lg transition-shadow">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-accent/10 border border-accent/20 mb-4">
              <BookOpen className="w-6 h-6 text-accent" />
            </div>
            <h3 className="text-lg font-semibold mb-2">User Guide</h3>
            <p className="text-muted-foreground text-sm mb-4">
              Comprehensive guide covering all RiftAI features and tips.
            </p>
            <Button variant="outline" className="w-full" disabled>
              Coming Soon
            </Button>
          </Card>
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 mb-8">
          <Button
            variant={selectedCategory === null ? "default" : "outline"}
            onClick={() => setSelectedCategory(null)}
            size="sm"
          >
            All Categories
          </Button>
          {faqCategories.map((category) => {
            const Icon = category.icon
            return (
              <Button
                key={category.id}
                variant={selectedCategory === category.id ? "default" : "outline"}
                onClick={() => setSelectedCategory(category.id)}
                size="sm"
                className="flex items-center gap-2"
              >
                <Icon className="w-4 h-4" />
                {category.title}
              </Button>
            )
          })}
        </div>

        {/* FAQ Sections */}
        <div className="space-y-8">
          {filteredCategories.map((category) => {
            const Icon = category.icon
            return (
              <div key={category.id}>
                <div className="flex items-center mb-6">
                  <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl ${category.bgColor} border mr-4`}>
                    <Icon className={`w-5 h-5 ${category.color}`} />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold">{category.title}</h2>
                    <p className="text-muted-foreground">
                      {category.questions.length} questions
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  {category.questions.map((faq, index) => (
                    <FAQItem
                      key={index}
                      question={faq.question}
                      answer={faq.answer}
                    />
                  ))}
                </div>
              </div>
            )
          })}
        </div>

        {/* No Results */}
        {filteredCategories.length === 0 && (
          <Card className="p-12 text-center">
            <HelpCircle className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No results found</h3>
            <p className="text-muted-foreground mb-6">
              Try adjusting your search terms or browse all categories.
            </p>
            <Button onClick={() => {
              setSearchQuery('')
              setSelectedCategory(null)
            }}>
              Clear Filters
            </Button>
          </Card>
        )}

        {/* Still Need Help */}
        <Card className="p-8 mt-12 text-center bg-gradient-to-r from-primary/5 to-secondary/5">
          <h2 className="text-2xl font-bold mb-4">Still Need Help?</h2>
          <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
            Our support team is available to help you get the most out of RiftAI. 
            Contact us and we'll get back to you within 24 hours.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" disabled>
              Coming Soon
            </Button>
            <Button variant="outline" size="lg" disabled>
              Coming Soon
            </Button>
          </div>
        </Card>
      </div>
    </Container>
  )
}
