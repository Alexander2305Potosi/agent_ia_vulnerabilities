import unittest
import re
from agent_ia.core.mutator import GradleMutator

class TestGradleMutator(unittest.TestCase):
    
    def setUp(self):
        self.mutator = GradleMutator()

    def test_substitute_literal_with_variable(self):
        """ Checks that literal dependencies are updated to variables and not deleted. """
        content = """
        dependencies {
            implementation 'io.netty:netty-codec-http:4.1.68.Final'
            testImplementation "org.junit:junit:4.13"
            implementation project(':')
        }
        """
        # Test Case 1: Standard implementation
        result, count = self.mutator.substitute_literal_with_variable(content, "io.netty:netty-codec-http", "nettyCodecHttpVersion")
        self.assertTrue(count)
        self.assertIn('implementation "io.netty:netty-codec-http:${nettyCodecHttpVersion}"', result)
        
        # Test Case 2: testImplementation with double quotes
        result, count = self.mutator.substitute_literal_with_variable(result, "org.junit:junit", "junitVersion")
        self.assertTrue(count)
        self.assertIn('testImplementation "org.junit:junit:${junitVersion}"', result)
        
        # Test Case 3: project(':') should NOT be touched
        self.assertIn("implementation project(':')", result)

    def test_inject_resolution_strategy_rule_formatting(self):
        """ Checks that rules are injected with correct indentation and headers (v2.0 standard). """
        content = """
        configurations.all {
            resolutionStrategy.eachDependency { DependencyResolveDetails details ->
                // Inject rules here
            }
        }
        """
        result, success = self.mutator.inject_resolution_strategy_rule(
            content, "io.netty:netty-codec", "nettyCodecVersion", "Danny: Fix CVE-2026-TEST"
        )
        
        self.assertTrue(success)
        # Check standard indentation (8 spaces for the 'if')
        self.assertIn("        if (details.requested.group == 'io.netty') {", result)
        # Check standard indentation (12 spaces for details)
        self.assertIn("            details.useVersion \"${nettyCodecVersion}\"", result)
        self.assertIn("            details.because \"Danny: Fix CVE-2026-TEST\"", result)
        # Check that we cleaned the placeholder if it was Step 2
        self.assertNotIn("// Inject rules here", result)

    def test_inject_resolution_strategy_rule_update_existing(self):
        """ Checks that existing rules are updated without breaking indentation. """
        content = """
        configurations.all {
            resolutionStrategy.eachDependency { DependencyResolveDetails details ->
                if (details.requested.group == 'io.netty') {
                    details.useVersion "${oldVersion}"
                    details.because "old reason"
                }
            }
        }
        """
        result, success = self.mutator.inject_resolution_strategy_rule(
            content, "io.netty:netty-codec", "nettyCodecVersion", "Danny: Updated Fix"
        )
        
        self.assertTrue(success)
        # Ensure it didn't keep the old indentation if it was different, or at least it's correct now
        self.assertIn("        if (details.requested.group == 'io.netty') {", result)
        self.assertIn("${nettyCodecVersion}", result)
        self.assertIn("Danny: Updated Fix", result)

if __name__ == '__main__':
    unittest.main()
