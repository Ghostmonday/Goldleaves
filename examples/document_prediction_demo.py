# examples/document_prediction_demo.py

"""
Document Prediction & Correction System Demo

This example demonstrates the complete workflow of Phase 5:
1. Creating documents with case/client relationships
2. Ingesting AI predictions
3. Applying human corrections
4. Tracking audit trails
5. Generating compliance reports

Run this after setting up the database and starting the API server.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any
import json


class DocumentPredictionDemo:
    """Demo client for document prediction system."""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: str = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.session = httpx.AsyncClient()
        
    async def authenticate(self, email: str, password: str) -> str:
        """Authenticate and get access token."""
        auth_data = {
            "email": email,
            "password": password
        }
        
        response = await self.session.post(f"{self.base_url}/auth/login", json=auth_data)
        if response.status_code == 200:
            token_data = response.json()
            self.auth_token = token_data["access_token"]
            return self.auth_token
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get headers with authorization."""
        if not self.auth_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    async def create_test_client(self) -> Dict[str, Any]:
        """Create a test client for documents."""
        client_data = {
            "name": "ACME Corporation",
            "type": "corporate",
            "industry": "Technology",
            "email": "legal@acme.com",
            "phone": "+1-555-0123",
            "address": {
                "line1": "123 Business Ave",
                "city": "San Francisco",
                "state_province": "CA",
                "postal_code": "94105",
                "country": "USA"
            }
        }
        
        response = await self.session.post(
            f"{self.base_url}/clients/",
            json=client_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            client = response.json()
            print(f"✅ Created test client: {client['name']} (ID: {client['id']})")
            return client
        else:
            raise Exception(f"Failed to create client: {response.text}")
    
    async def create_test_case(self, client_id: int) -> Dict[str, Any]:
        """Create a test case for documents."""
        case_data = {
            "title": "Contract Review & Analysis",
            "description": "Comprehensive review of service agreements and contracts",
            "status": "active",
            "priority": "high",
            "client_id": client_id,
            "estimated_hours": 40.0,
            "billing_rate": 350.00
        }
        
        response = await self.session.post(
            f"{self.base_url}/cases/",
            json=case_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            case = response.json()
            print(f"✅ Created test case: {case['title']} (ID: {case['id']})")
            return case
        else:
            raise Exception(f"Failed to create case: {response.text}")
    
    async def create_document_with_content(self, case_id: int, client_id: int) -> Dict[str, Any]:
        """Create a document with sample contract content."""
        document_data = {
            "title": "Service Agreement - ACME Corp",
            "description": "Professional services agreement for software development",
            "document_type": "contract",
            "status": "draft",
            "confidentiality": "confidential",
            "case_id": case_id,
            "client_id": client_id,
            "content": """
            SERVICE AGREEMENT
            
            This Service Agreement ("Agreement") is entered into on January 15, 2024,
            between ACME Corporation, a Delaware corporation ("Client"), and 
            Professional Services LLC, a California limited liability company ("Provider").
            
            1. SERVICES
            Provider agrees to provide software development and consulting services
            as detailed in Exhibit A attached hereto and incorporated by reference.
            
            2. TERM
            This Agreement shall commence on February 1, 2024, and continue for 
            a period of twelve (12) months, unless terminated earlier in accordance
            with the provisions herein.
            
            3. COMPENSATION
            Client agrees to pay Provider a total fee of $120,000, payable in 
            monthly installments of $10,000 due on the first day of each month.
            
            4. CONFIDENTIALITY
            Both parties acknowledge that confidential information may be disclosed
            during the performance of this Agreement and agree to maintain such
            information in strict confidence.
            
            5. TERMINATION
            Either party may terminate this Agreement with thirty (30) days written notice.
            """,
            "tags": ["contract", "service-agreement", "high-priority"],
            "metadata": {
                "contract_value": 120000,
                "term_months": 12,
                "auto_renewal": False,
                "governing_law": "California"
            }
        }
        
        response = await self.session.post(
            f"{self.base_url}/documents/",
            json=document_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            document = response.json()
            print(f"✅ Created document: {document['title']} (ID: {document['id']})")
            return document
        else:
            raise Exception(f"Failed to create document: {response.text}")
    
    async def ingest_ai_predictions(self, document_id: int) -> Dict[str, Any]:
        """Simulate AI prediction ingestion."""
        prediction_data = {
            "prediction_data": {
                "model_name": "legal-classifier-v3",
                "model_version": "3.2.1",
                "prediction_timestamp": datetime.utcnow().isoformat(),
                "overall_confidence": 0.89,
                "predictions": [
                    {
                        "field_name": "contract_type",
                        "predicted_value": "service_agreement",
                        "confidence": 0.92,
                        "field_type": "classification",
                        "alternatives": ["consulting_agreement", "professional_services"],
                        "reasoning": "Document contains service delivery terms and professional compensation structure"
                    },
                    {
                        "field_name": "contract_value",
                        "predicted_value": "120000",
                        "confidence": 0.95,
                        "field_type": "monetary_extraction",
                        "original_text": "total fee of $120,000",
                        "currency": "USD"
                    },
                    {
                        "field_name": "term_duration",
                        "predicted_value": "12_months",
                        "confidence": 0.88,
                        "field_type": "duration_extraction",
                        "original_text": "period of twelve (12) months"
                    },
                    {
                        "field_name": "termination_notice",
                        "predicted_value": "30_days",
                        "confidence": 0.85,
                        "field_type": "duration_extraction",
                        "original_text": "thirty (30) days written notice"
                    }
                ],
                "document_classification": "service_contract",
                "entities": [
                    "ACME Corporation",
                    "Professional Services LLC",
                    "Delaware corporation",
                    "California limited liability company"
                ],
                "key_phrases": [
                    "software development",
                    "consulting services", 
                    "confidential information",
                    "monthly installments",
                    "written notice"
                ],
                "risk_indicators": [
                    {
                        "type": "liability_concern",
                        "description": "Limited liability provisions may need review",
                        "severity": "medium",
                        "confidence": 0.75
                    },
                    {
                        "type": "auto_renewal",
                        "description": "No automatic renewal clause detected",
                        "severity": "low",
                        "confidence": 0.90
                    }
                ]
            },
            "auto_apply_high_confidence": False,
            "validation_required": True
        }
        
        response = await self.session.post(
            f"{self.base_url}/documents/{document_id}/predict",
            json=prediction_data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            document = response.json()
            print(f"✅ Ingested AI predictions (confidence: {document['prediction_score']:.2f})")
            return document
        else:
            raise Exception(f"Failed to ingest predictions: {response.text}")
    
    async def apply_human_corrections(self, document_id: int) -> Dict[str, Any]:
        """Apply human corrections to AI predictions."""
        correction_data = {
            "corrections": [
                {
                    "field_path": "contract_type",
                    "original_value": "service_agreement",
                    "corrected_value": "professional_services_agreement",
                    "confidence_before": 0.92,
                    "confidence_after": 1.0,
                    "correction_type": "edit",
                    "reasoning": "More specific classification based on service nature"
                },
                {
                    "field_path": "contract_value",
                    "original_value": "120000",
                    "corrected_value": "120000",
                    "confidence_before": 0.95,
                    "confidence_after": 1.0,
                    "correction_type": "confirm",
                    "reasoning": "Value confirmed accurate"
                },
                {
                    "field_path": "governing_law",
                    "original_value": None,
                    "corrected_value": "California",
                    "confidence_before": 0.0,
                    "confidence_after": 1.0,
                    "correction_type": "add",
                    "reasoning": "Added missing governing law from document metadata"
                }
            ],
            "correction_reason": "Human expert review and validation of AI predictions",
            "requires_review": False
        }
        
        response = await self.session.post(
            f"{self.base_url}/documents/{document_id}/correct",
            json=correction_data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            document = response.json()
            print(f"✅ Applied {len(correction_data['corrections'])} human corrections")
            return document
        else:
            raise Exception(f"Failed to apply corrections: {response.text}")
    
    async def get_audit_trail(self, document_id: int) -> Dict[str, Any]:
        """Get the audit trail for a document."""
        response = await self.session.get(
            f"{self.base_url}/documents/{document_id}/audit",
            headers=self.headers
        )
        
        if response.status_code == 200:
            audit_trail = response.json()
            print(f"✅ Retrieved audit trail with {len(audit_trail['recent_versions'])} versions")
            return audit_trail
        else:
            raise Exception(f"Failed to get audit trail: {response.text}")
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """Get organization document statistics."""
        response = await self.session.get(
            f"{self.base_url}/documents/stats/overview",
            headers=self.headers
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Retrieved document statistics")
            return stats
        else:
            raise Exception(f"Failed to get document stats: {response.text}")
    
    async def search_documents(self, query: str) -> list:
        """Search documents."""
        response = await self.session.get(
            f"{self.base_url}/documents/search/quick",
            params={"q": query},
            headers=self.headers
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results)} documents matching '{query}'")
            return results
        else:
            raise Exception(f"Failed to search documents: {response.text}")
    
    async def run_complete_demo(self):
        """Run the complete document prediction demo."""
        print("🚀 Starting Document Prediction & Correction System Demo")
        print("=" * 60)
        
        try:
            # Step 1: Authenticate (you'll need to provide credentials)
            print("\n📝 Step 1: Authentication")
            # self.auth_token = "your_token_here"  # Or call authenticate()
            
            # Step 2: Create test data
            print("\n📝 Step 2: Creating test client and case")
            client = await self.create_test_client()
            case = await self.create_test_case(client["id"])
            
            # Step 3: Create document with content
            print("\n📝 Step 3: Creating document with sample contract content")
            document = await self.create_document_with_content(case["id"], client["id"])
            
            # Step 4: Ingest AI predictions
            print("\n📝 Step 4: Ingesting AI predictions")
            predicted_document = await self.ingest_ai_predictions(document["id"])
            
            # Step 5: Apply human corrections
            print("\n📝 Step 5: Applying human corrections")
            corrected_document = await self.apply_human_corrections(document["id"])
            
            # Step 6: Get audit trail
            print("\n📝 Step 6: Retrieving audit trail")
            audit_trail = await self.get_audit_trail(document["id"])
            
            # Step 7: Get statistics
            print("\n📝 Step 7: Getting document statistics")
            stats = await self.get_document_stats()
            
            # Step 8: Search documents
            print("\n📝 Step 8: Searching documents")
            search_results = await self.search_documents("ACME")
            
            # Summary
            print("\n" + "=" * 60)
            print("✅ Demo completed successfully!")
            print(f"   • Created client: {client['name']}")
            print(f"   • Created case: {case['title']}")
            print(f"   • Created document: {document['title']}")
            print(f"   • Applied AI predictions with {predicted_document['prediction_score']:.2f} confidence")
            print(f"   • Processed {len(audit_trail['recent_corrections'])} human corrections")
            print(f"   • Generated audit trail with {audit_trail['current_version']} versions")
            print(f"   • Found {len(search_results)} matching documents")
            
            # Display key metrics
            print(f"\n📊 Organization Statistics:")
            print(f"   • Total documents: {stats['total_documents']}")
            print(f"   • High confidence predictions: {stats['high_confidence_count']}")
            print(f"   • Documents with corrections: {stats['documents_with_corrections']}")
            print(f"   • Average prediction score: {stats['average_prediction_score']:.2f}")
            
        except Exception as e:
            print(f"❌ Demo failed: {str(e)}")
            raise
        finally:
            await self.session.aclose()


async def main():
    """Run the demo."""
    demo = DocumentPredictionDemo()
    
    # You can either authenticate with credentials or set a token
    # await demo.authenticate("admin@example.com", "password123")
    # OR
    # demo.auth_token = "your_jwt_token_here"
    
    await demo.run_complete_demo()


if __name__ == "__main__":
    print("Document Prediction & Correction System Demo")
    print("============================================")
    print("This demo showcases the complete Phase 5 workflow:")
    print("• Document creation with case/client relationships")
    print("• AI prediction ingestion with confidence scoring")
    print("• Human-in-the-loop correction validation")
    print("• Comprehensive audit trail tracking")
    print("• Statistics and search capabilities")
    print("\nStarting demo...")
    
    asyncio.run(main())
