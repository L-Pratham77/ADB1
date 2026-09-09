# Schema.org JSON-LD Gold-Standard Templates

Structured data in JSON-LD format is the primary protocol by which AI search engines, RAG pipelines, and knowledge graph builders extract explicit, unambiguous factual triples without requiring natural language inference.

---

## 1. Organization Schema with Entity Corroboration (`sameAs`)

Place this on the homepage or About page to establish authoritative entity identity.

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Acme Cloud AI",
  "alternateName": "Acme AI",
  "legalName": "Acme Technologies, Inc.",
  "url": "https://example.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://example.com/assets/logo.png",
    "width": "600",
    "height": "60"
  },
  "description": "Acme Cloud AI provides enterprise automated data pipeline orchestration and telemetry analytics.",
  "foundingDate": "2021-04-15",
  "sameAs": [
    "https://www.wikidata.org/wiki/Q12345678",
    "https://en.wikipedia.org/wiki/Acme_Technologies",
    "https://www.linkedin.com/company/acme-technologies",
    "https://www.crunchbase.com/organization/acme-technologies",
    "https://twitter.com/acmetech",
    "https://github.com/acme-technologies"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-800-555-0199",
    "contactType": "customer service",
    "availableLanguage": ["en"]
  }
}
```

---

## 2. Product & Pricing Schema (`Product` / `Offer`)

Allows AI assistants to answer direct questions like *"How much does Acme cost?"* or *"What plans does Acme offer?"*.

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Acme Data Orchestrator Enterprise",
  "description": "Cloud-native data pipeline orchestrator with sub-second task scheduling and automated lineage.",
  "image": "https://example.com/assets/product-hero.png",
  "brand": {
    "@type": "Brand",
    "name": "Acme"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/pricing",
    "priceCurrency": "USD",
    "price": "99.00",
    "priceValidUntil": "2027-12-31",
    "availability": "https://schema.org/InStock",
    "category": "Enterprise Software Subscription"
  }
}
```

---

## 3. FAQPage Schema (Direct AI Quotation Engine)

AI assistants frequently extract direct Q&A pairs from `FAQPage` schemas for search snippets and conversational responses.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is Acme Data Orchestrator?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Acme Data Orchestrator is a cloud-native platform that automates dbt, BigQuery, and Spark pipelines with built-in telemetry."
      }
    },
    {
      "@type": "Question",
      "name": "Does Acme support SOC-2 Type II compliance?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Yes. Acme is fully SOC-2 Type II certified and complies with GDPR and HIPAA requirements."
      }
    }
  ]
}
```

---

## 4. BreadcrumbList Schema (Hierarchy & Context)

Establishes topical hierarchy so AI crawlers understand document parentage.

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://example.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Solutions",
      "item": "https://example.com/solutions"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Enterprise Analytics",
      "item": "https://example.com/solutions/enterprise-analytics"
    }
  ]
}
```
