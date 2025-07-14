import requests
import json
import time
from typing import Dict, Any

class LegalChatbotTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def test_health_check(self) -> Dict[str, Any]:
        """Test health check endpoint"""
        print("Testing health check...")
        try:
            response = requests.get(f"{self.base_url}/health")
            result = {
                "status_code": response.status_code,
                "response": response.json(),
                "success": response.status_code == 200
            }
            print(f"Health check: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            return result
        except Exception as e:
            print(f"Health check: ❌ FAILED - {e}")
            return {"success": False, "error": str(e)}
    
    def test_system_stats(self) -> Dict[str, Any]:
        """Test system stats endpoint"""
        print("Testing system stats...")
        try:
            response = requests.get(f"{self.base_url}/stats")
            result = {
                "status_code": response.status_code,
                "response": response.json(),
                "success": response.status_code == 200
            }
            print(f"System stats: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            if result['success']:
                stats = result['response']
                print(f"  - Total documents: {stats.get('total_documents', 0)}")
                print(f"  - Unique sources: {stats.get('unique_sources', 0)}")
                print(f"  - File types: {stats.get('file_types', [])}")
            return result
        except Exception as e:
            print(f"System stats: ❌ FAILED - {e}")
            return {"success": False, "error": str(e)}
    
    def test_legal_query(self, question: str) -> Dict[str, Any]:
        """Test a legal query"""
        print(f"Testing legal query: '{question[:50]}...'")
        try:
            payload = {
                "question": question,
                "include_sources": True,
                "max_sources": 3
            }
            
            start_time = time.time()
            response = requests.post(f"{self.base_url}/ask", json=payload)
            response_time = time.time() - start_time
            
            result = {
                "status_code": response.status_code,
                "response": response.json(),
                "response_time": round(response_time, 2),
                "success": response.status_code == 200
            }
            
            print(f"Legal query: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            
            if result['success']:
                resp_data = result['response']
                print(f"  - Answer length: {len(resp_data.get('answer', ''))}")
                print(f"  - Confidence score: {resp_data.get('confidence_score', 0)}")
                print(f"  - Sources used: {resp_data.get('context_used', 0)}")
                print(f"  - Query type: {resp_data.get('query_type', 'unknown')}")
                print(f"  - Response time: {resp_data.get('response_time', 0)}s")
            
            return result
            
        except Exception as e:
            print(f"Legal query: ❌ FAILED - {e}")
            return {"success": False, "error": str(e)}
    
    def test_term_explanation(self, term: str) -> Dict[str, Any]:
        """Test term explanation"""
        print(f"Testing term explanation: '{term}'")
        try:
            payload = {"term": term}
            
            response = requests.post(f"{self.base_url}/explain-term", json=payload)
            
            result = {
                "status_code": response.status_code,
                "response": response.json(),
                "success": response.status_code == 200
            }
            
            print(f"Term explanation: {'✅ PASSED' if result['success'] else '❌ FAILED'}")
            
            if result['success']:
                resp_data = result['response']
                print(f"  - Answer length: {len(resp_data.get('answer', ''))}")
                print(f"  - Confidence score: {resp_data.get('confidence_score', 0)}")
            
            return result
            
        except Exception as e:
            print(f"Term explanation: ❌ FAILED - {e}")
            return {"success": False, "error": str(e)}
    
    def run_comprehensive_test(self):
        """Run a comprehensive test suite"""
        print("=" * 60)
        print("LEGAL CHATBOT API COMPREHENSIVE TEST")
        print("=" * 60)
        
        # Test cases
        test_questions = [
            "What is the punishment for theft under IPC?",
            "Explain the concept of fundamental rights in Indian Constitution",
            "What are the grounds for divorce under Hindu Marriage Act?",
            "How to file a complaint in consumer court?",
            "What is the procedure for bail application?"
        ]
        
        test_terms = [
            "habeas corpus",
            "res judicata",
            "ultra vires",
            "mandamus"
        ]
        
        results = {
            "health_check": None,
            "system_stats": None,
            "legal_queries": [],
            "term_explanations": [],
            "overall_success": True
        }
        
        # Run tests
        print("\n1. HEALTH CHECK")
        print("-" * 30)
        results["health_check"] = self.test_health_check()
        if not results["health_check"]["success"]:
            results["overall_success"] = False
        
        print("\n2. SYSTEM STATS")
        print("-" * 30)
        results["system_stats"] = self.test_system_stats()
        if not results["system_stats"]["success"]:
            results["overall_success"] = False
        
        print("\n3. LEGAL QUERIES")
        print("-" * 30)
        for question in test_questions:
            result = self.test_legal_query(question)
            results["legal_queries"].append(result)
            if not result["success"]:
                results["overall_success"] = False
            time.sleep(1)  # Rate limiting
        
        print("\n4. TERM EXPLANATIONS")
        print("-" * 30)
        for term in test_terms:
            result = self.test_term_explanation(term)
            results["term_explanations"].append(result)
            if not result["success"]:
                results["overall_success"] = False
            time.sleep(1)  # Rate limiting
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = (
            1 +  # health check
            1 +  # system stats
            len(test_questions) +  # legal queries
            len(test_terms)  # term explanations
        )
        
        passed_tests = sum([
            1 if results["health_check"]["success"] else 0,
            1 if results["system_stats"]["success"] else 0,
            sum(1 for r in results["legal_queries"] if r["success"]),
            sum(1 for r in results["term_explanations"] if r["success"])
        ])
        
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
        
        if results["overall_success"]:
            print("\n🎉 ALL TESTS PASSED! The Legal Chatbot API is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please check the logs above.")
        
        return results

def main():
    """Main function to run tests"""
    tester = LegalChatbotTester()
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return
    
    # Run comprehensive tests
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()